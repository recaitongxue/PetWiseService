"""管理端接口冒烟：管理员登录 → 各看板/CRUD 接口 → 权限校验。"""
import json
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:8080/api/v1'
ADMIN_PHONE = '13900000000'
USER_PHONE = '13800138000'


def req(method, path, token=None, body=None):
    headers = {}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers['Content-Type'] = 'application/json'
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
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


def login(phone):
    res = req('POST', '/auth/login', body={'mode': 'sms', 'phone': phone, 'code': '888888'})
    return res.get('data', {}).get('accessToken'), res


def show(label, res, peek=110):
    code = res.get('code')
    d = res.get('data')
    if isinstance(d, list):
        s = 'list(%d)' % len(d)
    elif isinstance(d, dict):
        s = ','.join(list(d.keys())[:7])[:peek]
    else:
        s = str(d)[:peek]
    print('%s %-38s code=%s %s' % (
        'OK ' if code == 0 else 'FAIL', label, code, s if code == 0 else res.get('message')))
    return code == 0


tok, r = login(ADMIN_PHONE)
if not show('POST /auth/login (admin)', r):
    raise SystemExit('管理员登录失败')

fails = []
for p in ['/admin/overview', '/admin/announcements', '/admin/feedbacks', '/admin/users',
          '/admin/consults', '/admin/records', '/admin/reports', '/admin/settings']:
    if not show('GET ' + p, req('GET', p, tok)):
        fails.append(p)

# 公告 CRUD
c = req('POST', '/admin/announcements', tok, body={'title': '冒烟公告', 'content': '内容', 'level': 'info'})
show('POST /admin/announcements', c)
aid = (c.get('data') or {}).get('id')
if aid:
    show('PATCH /admin/announcements/{id}', req('PATCH', '/admin/announcements/%s' % aid, tok,
                                                body={'title': '冒烟公告(改)', 'pinned': True}))
    show('DELETE /admin/announcements/{id}', req('DELETE', '/admin/announcements/%s' % aid, tok))

# 反馈处理
fbs = (req('GET', '/admin/feedbacks?state=pending', tok).get('data') or {}).get('list') or []
if fbs:
    show('PATCH /admin/feedbacks/{id}', req('PATCH', '/admin/feedbacks/%s' % fbs[0]['id'], tok,
                                            body={'status': 'resolved'}))

# 举报处理
rps = (req('GET', '/admin/reports?status=pending', tok).get('data') or {}).get('list') or []
if rps:
    show('PATCH /admin/reports/{id}', req('PATCH', '/admin/reports/%s' % rps[0]['id'], tok,
                                          body={'status': 'resolved'}))

# 识别纠正审核
rcs = (req('GET', '/admin/records', tok).get('data') or {}).get('list') or []
if rcs:
    show('PATCH /admin/records/{id}', req('PATCH', '/admin/records/%s' % rcs[0]['id'], tok,
                                          body={'status': 'confirmed'}))

# 用户管理
us = (req('GET', '/admin/users', tok).get('data') or {}).get('list') or []
if us:
    show('PATCH /admin/users/{id}', req('PATCH', '/admin/users/%s' % us[0]['id'], tok,
                                        body={'bio': '冒烟更新'}))

show('PUT /admin/settings', req('PUT', '/admin/settings', tok, body={'aiDailyFree': 5}))

# 权限校验：普通用户不得访问管理端
utok, _ = login(USER_PHONE)
res = req('GET', '/admin/overview', utok)
denied = res.get('code') != 0
print('%s 普通用户访问 /admin/overview 被拦截 code=%s' % (
    'OK ' if denied else 'FAIL', res.get('code')))
if not denied:
    fails.append('admin 权限校验')

print('\n===== 管理端失败项 %d =====' % len(fails))
for f in fails:
    print('  FAIL:', f)
