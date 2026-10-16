"""前端联调冒烟：登录后逐个调用前端 @/api/data 实际用到的接口，校验 code=0。

契约变更（v1.0 清理后）：
- 删除 /home、/consult/modes、/consult/departments、/consult/dictionary、
  /pets/{id}/reminders 的调用（后端已删这些端点）
- 新增 /wallet 钱包流水、点赞切换、问诊单评价闭环的真实性断言
"""
import json
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:8080/api/v1'


def req(method, path, token=None, body=None, raw=None, ctype=None):
    url = BASE + path
    headers = {}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers['Content-Type'] = 'application/json'
    if raw is not None:
        data = raw
        headers['Content-Type'] = ctype
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return json.loads(resp.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode() or '{}')
        except Exception:
            return {'code': -1, 'message': 'HTTP %s' % e.code}
    except Exception as e:
        return {'code': -1, 'message': str(e)}


def show(label, res, peek=90):
    code = res.get('code')
    ok = 'OK ' if code == 0 else 'FAIL'
    d = res.get('data')
    if isinstance(d, list):
        s = 'list(%d)' % len(d)
    elif isinstance(d, dict):
        s = ','.join(list(d.keys())[:6])
        s = s[:peek]
    else:
        s = str(d)[:peek]
    print('%s %-34s code=%s %s' % (ok, label, code, s if code == 0 else res.get('message')))
    return code == 0


# ---------- 登录 ----------
res = req('POST', '/auth/login', body={'phone': '13800138000', 'code': '888888'})
tok = res.get('data', {}).get('accessToken')
fails = []
if not show('POST /auth/login', res):
    raise SystemExit('登录失败，后续无法继续')

# ---------- GET ----------
gets = [
    '/users/me', '/pets', '/schedule', '/schedule/types',
    '/breeds', '/doctors', '/posts', '/conversations', '/contacts',
    '/favorites', '/recognitions', '/announcements', '/memo', '/wallet',
    '/consult/ai-quota', '/consult/orders', '/consult/reports',
]
for p in gets:
    r = req('GET', p, tok)
    if not show('GET ' + p, r):
        fails.append(p)

pets = req('GET', '/pets', tok).get('data') or []
pid = pets[0]['id'] if pets else 1
for p in ['/pets/%s' % pid, '/pets/%s/health-trend' % pid, '/pets/%s/weights' % pid,
          '/pets/%s/records' % pid]:
    r = req('GET', p, tok)
    if not show('GET ' + p, r):
        fails.append(p)

convs = req('GET', '/conversations', tok).get('data') or []
if convs:
    r = req('GET', '/conversations/%s/messages' % convs[0]['id'], tok)
    show('GET /conversations/{id}/messages', r)

posts = req('GET', '/posts', tok).get('data')
plist = posts.get('list') if isinstance(posts, dict) else posts
if plist:
    r = req('GET', '/posts/%s/comments' % plist[0]['id'], tok)
    show('GET /posts/{id}/comments', r)

doctors = req('GET', '/doctors', tok).get('data') or []
doc_id = doctors[0]['id'] if doctors else None
if doc_id:
    for p in ['/doctors/%s' % doc_id, '/doctors/%s/reviews' % doc_id]:
        show('GET ' + p, req('GET', p, tok))

breeds = req('GET', '/breeds', tok).get('data') or []
if breeds:
    show('GET /breeds/{id}', req('GET', '/breeds/%s' % breeds[0]['id'], tok))

# ---------- 钱包：充值 / 提现闭环（余额与流水真实对账） ----------
w0 = req('GET', '/wallet', tok).get('data') or {}
bal0 = w0.get('balance')
top = req('POST', '/wallet/topup', tok, body={'amount': 10, 'note': '冒烟充值'})
show('POST /wallet/topup', top)
bal1 = (top.get('data') or {}).get('balance')
wd = req('POST', '/wallet/withdraw', tok, body={'amount': 3.5, 'note': '冒烟提现'})
show('POST /wallet/withdraw', wd)
bal2 = (wd.get('data') or {}).get('balance')
print('     钱包：%s +10 -3.5 = %s %s' % (
    bal0, bal2,
    'OK 对账一致' if bal1 == bal0 + 10 and bal2 == bal1 - 3.5 else 'FAIL 余额不平'))
if not (bal1 == bal0 + 10 and bal2 == bal1 - 3.5):
    fails.append('wallet-balance')
w1 = req('GET', '/wallet', tok).get('data') or []
if w1.get('total', 0) < w0.get('total', 0) + 2:
    fails.append('wallet-tx')
    print('     FAIL 流水未落库')
over = req('POST', '/wallet/withdraw', tok, body={'amount': 999999})
print('     超额提现被拒：%s' % ('OK' if over.get('code') != 0 else 'FAIL 未拦截'))
if over.get('code') == 0:
    fails.append('wallet-overdraft')

# ---------- 社区：每用户点赞切换 ----------
if plist:
    post_id = plist[0]['id']
    base = req('GET', '/posts', tok).get('data')
    base_list = base.get('list') if isinstance(base, dict) else base
    likes0 = next((p['likes'] for p in base_list if p['id'] == post_id), None)
    liked0 = next((p.get('liked') for p in base_list if p['id'] == post_id), None)
    r1 = req('POST', '/posts/%s/like' % post_id, tok)
    show('POST /posts/{id}/like（切换）', r1)
    d1 = r1.get('data') or {}
    r2 = req('POST', '/posts/%s/like' % post_id, tok)
    d2 = r2.get('data') or {}
    print('     点赞切换：liked %s -> %s -> %s；likes %s -> %s -> %s %s' % (
        liked0, d1.get('liked'), d2.get('liked'),
        likes0, d1.get('likes'), d2.get('likes'),
        'OK 切换后回归原状' if d1.get('liked') != d2.get('liked')
        and d2.get('liked') == liked0 and d2.get('likes') == likes0 else 'FAIL 状态/计数异常'))
    if not (d1.get('liked') != d2.get('liked')
            and d2.get('liked') == liked0 and d2.get('likes') == likes0):
        fails.append('like-toggle')

# ---------- 问诊单全流程：下单 -> 发消息 -> 结束 -> 评价（医生评分取真实均值） ----------
if doc_id and pets:
    order = req('POST', '/consult/orders', tok, body={
        'doctorId': doc_id, 'petId': pid, 'mode': 'text', 'price': 19,
        'summary': {'chief': '冒烟问诊'}})
    show('POST /consult/orders', order)
    oid = (order.get('data') or {}).get('id')
    if oid:
        req('POST', '/consult/orders/%s/messages' % oid, tok, body={'text': '冒烟测试消息'})
        cl = req('POST', '/consult/orders/%s/close' % oid, tok)
        show('POST /consult/orders/{id}/close', cl)
        rv_before = req('GET', '/doctors/%s/reviews' % doc_id, tok).get('data') or {}
        n_before = rv_before.get('total', 0)
        rt = req('POST', '/consult/orders/%s/rating' % oid, tok,
                 body={'score': 4, 'tags': ['冒烟']})
        show('POST /consult/orders/{id}/rating', rt)
        # 再次评价：更新而非重复插入（order_id 唯一）
        again = req('POST', '/consult/orders/%s/rating' % oid, tok, body={'score': 2})
        show('POST /consult/orders/{id}/rating（改分）', again)
        rv_after = req('GET', '/doctors/%s/reviews' % doc_id, tok).get('data') or {}
        n_after = rv_after.get('total', 0)
        after = req('GET', '/doctors/%s' % doc_id, tok).get('data') or {}
        scores = [r.get('rating') for r in (rv_after.get('list') or [])]
        expect = round(sum(scores) / len(scores), 1) if scores else None
        print('     评价：%d -> %d 条（不重复插入）；评分=%s 期望=%s %s' % (
            n_before, n_after, after.get('rating'), expect,
            'OK 均值一致' if n_after == n_before + 1 and after.get('rating') == expect
            else 'FAIL 计数或评分不符'))
        if not (n_after == n_before + 1 and after.get('rating') == expect):
            fails.append('rating-flow')

# ---------- 写路径：AI 分诊与额度扣减 ----------
q1 = req('GET', '/consult/ai-quota', tok)
left1 = q1.get('data', {}).get('left')
r = req('POST', '/consult/triage', tok, body={'text': '狗狗一直呕吐还拉血'})
show('POST /consult/triage', r)
tr = (r.get('data') or {}).get('triage') or {}
print('     分诊字段：level=%s causes=%d dept=%s %s' % (
    tr.get('level'), len(tr.get('causes') or []), tr.get('dept'),
    'OK 字段齐全' if tr.get('causes') and tr.get('dept') else 'FAIL 缺 causes/dept'))
if not (tr.get('causes') and tr.get('dept')):
    fails.append('triage-fields')
q2 = req('GET', '/consult/ai-quota', tok)
left2 = q2.get('data', {}).get('left')
print('     额度：分诊前 left=%s -> 分诊后 left=%s %s' % (
    left1, left2, 'OK 已扣减' if left2 == left1 - 1 else 'FAIL 未扣减'))
if left2 != left1 - 1:
    fails.append('ai-quota')

# ---------- 写路径：收藏增删 ----------
add = req('POST', '/favorites', tok, body={'kind': 'breed', 'targetId': 'smoke-breed',
                                           'title': '冒烟品种', 'desc': 'smoke', 'route': '/breed/smoke'})
show('POST /favorites', add)
favs = (req('GET', '/favorites', tok).get('data') or [])
tid = add.get('data', {}).get('targetId')
print('     新增收藏 targetId=%s；列表含 targetId=%s' % (
    tid, 'OK' if any(f.get('targetId') == tid for f in favs) else 'FAIL'))
dres = req('DELETE', '/favorites/breed/%s' % tid, tok)
show('DELETE /favorites/breed/{targetId}', dres)
after = (req('GET', '/favorites', tok).get('data') or [])
print('     删除后仍存在=%s %s' % (
    any(f.get('targetId') == tid for f in after),
    'FAIL 未真正删除' if any(f.get('targetId') == tid for f in after) else 'OK 已删除'))

# ---------- 写路径：结构化预问诊 ----------
pc = req('POST', '/consult/pre-consult', tok, body={
    'petId': pid, 'partId': 'skin', 'symptomIds': ['skin-itch'],
    'symptomLabels': ['频繁挠抓或蹭蹭'], 'durationId': '2-3d',
    'durationLabel': '2–3 天', 'severityId': 'mild',
    'severityLabel': '轻微 · 吃喝玩正常', 'accompanyIds': [],
    'accompanyLabels': [], 'note': '冒烟测试'})
show('POST /consult/pre-consult', pc)
rid = (pc.get('data') or {}).get('reportId')
if rid:
    rd = req('GET', '/consult/reports/%s' % rid, tok)
    chief = (rd.get('data') or {}).get('chief') or {}
    print('     报告 chief.symptomLabels=%s %s' % (
        chief.get('symptomLabels'),
        'OK 中文标签' if chief.get('symptomLabels') == ['频繁挠抓或蹭蹭'] else 'FAIL 仍是 id'))

# ---------- 写路径：拍照识别（multipart 上传） ----------
boundary = '----smokeboundary'
img = b'\x89PNG\r\n\x1a\n' + b'0' * 64
body = (('--%s\r\nContent-Disposition: form-data; name="file"; filename="smoke.png"\r\n'
         'Content-Type: image/png\r\n\r\n' % boundary).encode()
        + img + ('\r\n--%s\r\nContent-Disposition: form-data; name="species"\r\n\r\ncat\r\n'
                 '--%s--\r\n' % (boundary, boundary)).encode())
rec = req('POST', '/recognitions', tok, raw=body, ctype='multipart/form-data; boundary=' + boundary)
show('POST /recognitions (upload)', rec)
print('     识别诚实标记 demo=%s' % (rec.get('data') or {}).get('demo'))

print('\n===== 结果：失败项 %d =====' % len(fails))
for f in fails:
    print('  FAIL:', f)
