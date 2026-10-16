/*
 * static.js —— 纯静态配置（无后端对应的固定选项 / 文案 / 示例）
 *
 * 2026-10-16 从 mock.js 抽出：原 mock.js 里的演示数据（用户 / 宠物 / 动态 / 会话等）
 * 已全部改为真实接口（见 @/api/data），这里只留真正静态的配置项。
 */

/* ============ 首页 ============ */
export const quickActions = [
  { id: 'scan', label: '拍照识别', sub: '品种 · 体态 · 状态', icon: 'camera', to: '/recognize', accent: true },
  { id: 'ask', label: '智能问诊', sub: 'AI 免费 3 次/日', icon: 'stethoscope', to: '/consult/ai' },
  { id: 'doctor', label: '找真人医生', sub: '图文 · 电话 · 视频', icon: 'verified', to: '/doctors' },
  { id: 'community', label: '宠物社区', sub: '晒一晒它', icon: 'paw', to: '/community' },
  { id: 'record', label: '健康档案', sub: '记录与日程', icon: 'heart', to: '/pet/mochi' }
]

export const tips = [
  {
    id: 1,
    tag: '今日贴士',
    title: '换季掉毛期',
    body: '每日梳毛 5 分钟可促进血液循环，减少毛球症发生。',
    tone: 'sage'
  },
  {
    id: 2,
    tag: '喂养提醒',
    title: '分餐更科学',
    body: '成年猫建议每日 2–3 餐少量多次，避免一次性暴食。',
    tone: 'peach'
  }
]


/* ============ 拍照识别 ============ */
export const recognitionSamples = [
  {
    id: 'r1',
    title: '英国短毛猫',
    sci: 'Felis catus',
    confidence: 0.96,
    species: 'cat',
    alternatives: [
      { title: '英国短毛猫', confidence: 0.96 },
      { title: '苏格兰折耳猫', confidence: 0.02 },
      { title: '中华田园猫', confidence: 0.01 }
    ]
  },
  {
    id: 'r2',
    title: '柯基犬',
    sci: 'Canis lupus familiaris',
    confidence: 0.93,
    species: 'dog',
    alternatives: [
      { title: '柯基犬', confidence: 0.93 },
      { title: '瑞典柯基犬', confidence: 0.03 },
      { title: '博美犬', confidence: 0.01 }
    ]
  },
  {
    id: 'r3',
    title: '布偶猫',
    sci: 'Felis catus',
    confidence: 0.91,
    species: 'cat',
    alternatives: [
      { title: '布偶猫', confidence: 0.91 },
      { title: '伯曼猫', confidence: 0.05 },
      { title: '土耳其安哥拉猫', confidence: 0.01 }
    ]
  }
]

/* ============ AI 问诊 ============ */
export const consultSeed = [
  {
    role: 'ai',
    text: '你好，我是 Petwise 智能兽医助手。可以描述宠物的情况，或上传一张照片让我看看。',
    time: '09:24'
  }
]

export const consultSuggestions = [
  '狗狗一直挠耳朵是怎么回事？',
  '猫咪最近不爱吃饭怎么办？',
  '帮我看看这张皮肤照片',
  '幼猫疫苗时间表'
]

/* ============================================================
   问诊模块：科室 / 医生 / AI 分诊规则 / 症状快捷标签
   ============================================================ */

export const symptomGroups = [
  { group: '消化', items: ['呕吐', '软便腹泻', '食欲下降', '便秘'] },
  { group: '皮肤', items: ['频繁挠抓', '脱毛斑秃', '皮肤红疹', '皮屑增多'] },
  { group: '头颈', items: ['挠耳朵', '眼屎增多', '打喷嚏', '口臭流涎'] },
  { group: '全身', items: ['精神萎靡', '跛行', '体重骤变', '呼吸异常'] }
]


/* ============ 问诊表单配置 ============ */
export const consultModes = [
  {
    id: 'text',
    label: '图文问诊',
    icon: 'comment',
    price: 19,
    desc: '上传照片与描述，医生 24h 内回复，可追问 3 次',
    eta: '平均 8 分钟接诊'
  },
  {
    id: 'voice',
    label: '电话问诊',
    icon: 'phone',
    price: 39,
    desc: '预约时段后医生直接致电，适合需要详细沟通',
    eta: '15 分钟通话'
  },
  {
    id: 'video',
    label: '视频问诊',
    icon: 'video',
    price: 59,
    desc: '面对面看诊，可实时展示患处与宠物状态',
    eta: '20 分钟通话'
  }
]

export const departments = [
  { id: 'all', label: '全部', icon: 'stethoscope' },
  { id: 'internal', label: '犬猫内科', icon: 'heart' },
  { id: 'surgery', label: '外科骨科', icon: 'firstaid' },
  { id: 'derma', label: '皮肤病', icon: 'sparkle' },
  { id: 'er', label: '急诊重症', icon: 'alert' },
  { id: 'exotic', label: '异宠专科', icon: 'paw' },
  { id: 'nutrition', label: '营养体重', icon: 'scale' },
  { id: 'eye', label: '眼科', icon: 'eye' }
]


/* ============ 预问诊问卷 ============ */
export const bodyParts = [
  {
    id: 'head',
    label: '头颈五官',
    icon: 'paw',
    symptoms: [
      { id: 'ear-itch', label: '频繁挠耳朵' },
      { id: 'ear-discharge', label: '耳道有分泌物或异味' },
      { id: 'eye-discharge', label: '眼屎增多 / 眯眼' },
      { id: 'sneeze', label: '打喷嚏 / 流鼻涕' },
      { id: 'mouth', label: '口臭 / 流涎 / 拒食硬物' },
      { id: 'head-tilt', label: '头部歪斜 / 转圈' }
    ]
  },
  {
    id: 'skin',
    label: '皮肤被毛',
    icon: 'sparkle',
    symptoms: [
      { id: 'skin-itch', label: '频繁挠抓或蹭蹭' },
      { id: 'skin-loss', label: '脱毛 / 斑秃' },
      { id: 'skin-rash', label: '红疹 / 皮屑增多' },
      { id: 'skin-lump', label: '摸到肿块' },
      { id: 'skin-lick', label: '持续舔同一部位' }
    ]
  },
  {
    id: 'digest',
    label: '消化系统',
    icon: 'heart',
    symptoms: [
      { id: 'vomit', label: '呕吐' },
      { id: 'diarrhea', label: '软便 / 腹泻' },
      { id: 'appetite', label: '食欲下降 / 拒食' },
      { id: 'constipation', label: '便秘 / 排便困难' },
      { id: 'blood-stool', label: '便中带血', redFlag: false, weight: 2 }
    ]
  },
  {
    id: 'breath',
    label: '呼吸循环',
    icon: 'heart',
    symptoms: [
      { id: 'cough', label: '咳嗽' },
      { id: 'breath-fast', label: '呼吸急促', weight: 2 },
      { id: 'breath-open', label: '张嘴呼吸 / 喘不上气', redFlag: true },
      { id: 'pale', label: '舌色发白或发紫', redFlag: true },
      { id: 'faint', label: '运动后虚脱 / 晕厥', redFlag: true }
    ]
  },
  {
    id: 'limb',
    label: '四肢骨骼',
    icon: 'paw',
    symptoms: [
      { id: 'lame', label: '跛行 / 抬腿' },
      { id: 'no-jump', label: '不愿跳跃或上下楼' },
      { id: 'joint', label: '关节肿胀 / 触碰疼痛' },
      { id: 'paw', label: '爪垫受伤 / 趾间红肿' },
      { id: 'paralysis', label: '后肢无力 / 无法站立', redFlag: true }
    ]
  },
  {
    id: 'urinary',
    label: '泌尿系统',
    icon: 'heart',
    symptoms: [
      { id: 'urine-freq', label: '尿频 / 到处乱尿' },
      { id: 'urine-blood', label: '尿中带血' },
      { id: 'urine-block', label: '排尿困难 / 尿不出来', redFlag: true },
      { id: 'drink', label: '饮水量明显变化' }
    ]
  },
  {
    id: 'behavior',
    label: '行为精神',
    icon: 'sparkle',
    symptoms: [
      { id: 'spirit-low', label: '精神萎靡 / 嗜睡' },
      { id: 'hide', label: '躲藏 / 不愿互动' },
      { id: 'aggression', label: '性情改变 / 攻击性' },
      { id: 'fit', label: '抽搐 / 意识丧失', redFlag: true }
    ]
  },
  {
    id: 'other',
    label: '其他',
    icon: 'notes',
    symptoms: [
      { id: 'weight-loss', label: '体重明显下降' },
      { id: 'weight-gain', label: '体重持续上升' },
      { id: 'poison', label: '疑似误食异物或毒物', redFlag: true },
      { id: 'trauma', label: '外伤 / 车祸 / 坠落', redFlag: true },
      { id: 'postop', label: '术后或产后护理' }
    ]
  }
]

export const durations = [
  { id: 'today', label: '今天刚开始', w: 0 },
  { id: '2-3d', label: '2–3 天', w: 1 },
  { id: '1w', label: '约一周', w: 2 },
  { id: '1w+', label: '超过一周', w: 3 }
]

export const severities = [
  { id: 'mild', label: '轻微 · 吃喝玩正常', w: 0 },
  { id: 'mid', label: '明显不适 · 但能进食', w: 2 },
  { id: 'severe', label: '精神差 · 不吃不喝', w: 4 }
]

export const accompanyOptions = [
  { id: 'spirit', label: '精神萎靡', w: 3 },
  { id: 'appetite', label: '食欲下降', w: 3 },
  { id: 'fever', label: '身体发热 / 耳朵发烫', w: 2 },
  { id: 'vomit-ac', label: '呕吐', w: 2 },
  { id: 'diarrhea-ac', label: '腹泻', w: 2 },
  { id: 'drink-ac', label: '饮水异常', w: 1 },
  { id: 'sleep', label: '睡眠增多 / 躲藏', w: 1 }
]
