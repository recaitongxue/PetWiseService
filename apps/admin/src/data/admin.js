// ============================================================
// Petwise Admin · 演示数据（接入后端后由接口替换）
// ============================================================

export const admin = {
  name: '平台运营',
  role: '超级管理员'
}

// 看板：核心指标
export const stats = [
  { key: 'users', label: '注册用户', value: 12846, delta: '+3.2%', dir: 'up', hint: '较上周' },
  { key: 'pets', label: '在档宠物', value: 17230, delta: '+2.8%', dir: 'up', hint: '较上周' },
  { key: 'recog', label: '今日识别', value: 1342, delta: '+12.6%', dir: 'up', hint: 'CV 调用量' },
  { key: 'consult', label: '今日问诊', value: 386, delta: '-1.4%', dir: 'down', hint: '大模型会话' }
]

// 看板：近 7 日识别 / 问诊调用（折线）
export const usageSeries = {
  days: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  recognize: [820, 932, 1010, 1290, 1330, 1520, 1342],
  consult: [240, 272, 241, 334, 390, 430, 386]
}

// 看板：品种识别分布（横向条）
export const breedDist = [
  { name: '英国短毛猫', pct: 26 },
  { name: '中华田园犬', pct: 22 },
  { name: '金毛寻回犬', pct: 17 },
  { name: '布偶猫', pct: 14 },
  { name: '柯基犬', pct: 12 },
  { name: '其他', pct: 9 }
]

// 用户管理
export const users = [
  { id: 'u1001', name: '林小满', phone: '138****2261', pets: 2, joined: '2025-11-03', state: 'active' },
  { id: 'u1002', name: '柯基豆豆妈', phone: '159****8834', pets: 1, joined: '2025-12-18', state: 'active' },
  { id: 'u1003', name: '橘座铲屎团', phone: '186****5102', pets: 3, joined: '2026-01-09', state: 'active' },
  { id: 'u1004', name: '新手铲屎官', phone: '135****7745', pets: 1, joined: '2026-02-22', state: 'frozen' },
  { id: 'u1005', name: '兽医老张', phone: '137****9021', pets: 0, joined: '2025-10-30', state: 'active', role: '兽医' },
  { id: 'u1006', name: '遛弯不拴绳', phone: '188****3319', pets: 1, joined: '2026-03-14', state: 'frozen' }
]

// 宠物管理
export const pets = [
  { id: 'p2001', name: '麻薯', species: '猫', breed: '英国短毛猫', owner: '林小满', age: 3, weight: 4.6, score: 86, state: 'good' },
  { id: 'p2002', name: '豆豆', species: '狗', breed: '柯基犬', owner: '柯基豆豆妈', age: 2, weight: 11.2, score: 78, state: 'watch' },
  { id: 'p2003', name: '煤球', species: '猫', breed: '中华田园猫', owner: '橘座铲屎团', age: 5, weight: 5.1, score: 91, state: 'good' },
  { id: 'p2004', name: '年糕', species: '猫', breed: '布偶猫', owner: '新手铲屎官', age: 1, weight: 3.8, score: 88, state: 'good' },
  { id: 'p2005', name: '坦克', species: '狗', breed: '金毛寻回犬', owner: '遛弯不拴绳', age: 4, weight: 31.5, score: 72, state: 'watch' }
]

// 识别记录（CV 调用日志）
// state: done 已完成 / review 用户手动纠正待审核 / approved 已采纳（可导出训练集）/ rejected 已驳回 / failed 识别失败
// corrected: 用户纠正后的品种（predicted 为模型原预测）
export const recognitions = [
  { id: 'r9001', user: '林小满', pet: '麻薯', breed: '英国短毛猫', conf: 0.96, time: '17:12', state: 'done' },
  { id: 'r9002', user: '柯基豆豆妈', pet: '豆豆', breed: '柯基犬', conf: 0.93, time: '16:45', state: 'done' },
  { id: 'r9003', user: '橘座铲屎团', pet: '煤球', breed: '中华田园猫', conf: 0.88, time: '16:31', state: 'done' },
  { id: 'r9004', user: '新手铲屎官', pet: '年糕', breed: '布偶猫', conf: 0.42, time: '16:02', state: 'review' },
  { id: 'r9005', user: '遛弯不拴绳', pet: '坦克', breed: '金毛寻回犬', conf: 0.91, time: '15:47', state: 'done' },
  { id: 'r9006', user: '匿名用户', pet: '—', breed: '无法识别', conf: 0.18, time: '15:20', state: 'failed' },
  { id: 'rc-demo1', user: '柯基豆豆妈', pet: '豆豆', breed: '瑞典柯基犬', predicted: '柯基犬', conf: 0.61, time: '今天 16:40', state: 'review' },
  { id: 'rc-demo2', user: '橘座铲屎团', pet: '煤球', breed: '英国短毛猫', predicted: '中华田园猫', conf: 0.58, time: '今天 15:22', state: 'review' },
  { id: 'rc-demo3', user: '林小满', pet: '麻薯', breed: '苏格兰折耳猫', predicted: '英国短毛猫', conf: 0.79, time: '昨天 21:03', state: 'approved' }
]

// 社区内容审核
export const posts = [
  { id: 'p7001', author: '阿橘的日常', text: '麻薯今天第一次主动跳上猫爬架顶端，老母亲甚感欣慰。', images: 3, time: '12 分钟前', state: 'pass' },
  { id: 'p7002', author: '柯基豆豆', text: '用 Petwise 拍了张照，识别说体态偏重哈哈。', images: 2, time: '1 小时前', state: 'pass' },
  { id: 'p7003', author: '推广小王子', text: '低价宠物药品，加微信 XXXXXX 私聊。', images: 1, time: '26 分钟前', state: 'pending' },
  { id: 'p7004', author: '匿名吐槽', text: '（含侮辱性言论，已命中敏感词库）', images: 0, time: '40 分钟前', state: 'pending' },
  { id: 'p7005', author: '兽医老张', text: '换季提醒：猫咪频繁打喷嚏、流泪，先排查环境粉尘与温差。', images: 0, time: '3 小时前', state: 'pass' }
]

// 问诊记录（大模型会话）
export const consults = [
  { id: 'c8001', user: '柯基豆豆妈', pet: '豆豆', topic: '频繁挠耳', turns: 8, model: 'GLM-4V', time: '17:05', state: 'done' },
  { id: 'c8002', user: '林小满', pet: '麻薯', topic: '软便观察', turns: 12, model: 'GLM-4V', time: '16:38', state: 'done' },
  { id: 'c8003', user: '新手铲屎官', pet: '年糕', topic: '疫苗时间表', turns: 5, model: 'GLM-4', time: '15:52', state: 'done' },
  { id: 'c8004', user: '橘座铲屎团', pet: '煤球', topic: '皮肤红肿（含图）', turns: 9, model: 'GLM-4V', time: '15:11', state: 'transferred' },
  { id: 'c8005', user: '遛弯不拴绳', pet: '坦克', topic: '挑食', turns: 3, model: 'GLM-4', time: '14:40', state: 'done' }
]

// 兽医管理（医生账号）
export const doctors = [
  { id: 'd9001', name: '兽医老张', dept: '猫科内科', hospital: '爱诺德动物医院', phone: '137****9021', online: true, consults: 1286, rating: 4.9, state: 'active', joined: '2025-10-30' },
  { id: 'd9002', name: '李医生', dept: '外科', hospital: '瑞鹏宠物医院中心店', phone: '138****1023', online: true, consults: 942, rating: 4.8, state: 'active', joined: '2025-11-12' },
  { id: 'd9003', name: '王医生', dept: '皮肤科', hospital: '芭比堂动物医院', phone: '139****5566', online: false, consults: 678, rating: 4.7, state: 'active', joined: '2026-01-05' },
  { id: 'd9004', name: '赵大夫', dept: '异宠专科', hospital: '爱诺德动物医院', phone: '150****7788', online: false, consults: 213, rating: 4.6, state: 'frozen', joined: '2026-03-20' }
]

// CV 模型状态（读取 cv/ 真实训练配置）
export const modelStatus = [
  { kind: 'dog', name: '狗 · 品种识别', backbone: 'convnext_large', classes: 130, note: 'cb_focal 长尾均衡 · @384' },
  { kind: 'cat', name: '猫 · 品种识别', backbone: 'efficientnet_v2_l', classes: 60, note: 'cb_focal 长尾均衡 · @384' }
]

// AI 内容审核：敏感词库（演示版，接后端后由模型 + 词库双通道）
export const sensitiveWords = [
  '微信', 'VX', 'vx', '加我', '私聊', '低价', '促销', '优惠', '代购',
  '辱骂', '垃圾', '该死', '打死',
  '赌博', '色情', '毒品'
]
