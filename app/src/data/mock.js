// ============================================================
// Petwise · 演示数据（前端 Mock，后端接口就绪后替换）
// ============================================================

export const user = {
  name: '林小满',
  handle: '@manman',
  initials: '满', // 个人头像用首字花押，离线可用；接入后改图片 URL
  bio: '两只猫的铲屎官 · 关注宠物健康',
  followers: 328,
  following: 156
}

export const pets = [
  {
    id: 'mochi',
    name: '麻薯',
    species: 'cat',
    breed: '英国短毛猫',
    age: 3,
    weight: 4.6,
    gender: '母',
    tagline: '今日心情：慵懒',
    healthScore: 86,
    nextVaccine: '2026-11-02',
    birthday: '2023-04-18'
  },
  {
    id: 'doudou',
    name: '豆豆',
    species: 'dog',
    breed: '柯基犬',
    age: 2,
    weight: 11.2,
    gender: '公',
    tagline: '今日心情：兴奋',
    healthScore: 78,
    nextVaccine: '2026-10-22',
    birthday: '2024-06-09'
  }
]

// 健康环形日历数据（按宠物区分趋势）
export const weeklyHealth = [
  { day: '一', value: 92, label: '优' },
  { day: '二', value: 88, label: '良' },
  { day: '三', value: 74, label: '需关注' },
  { day: '四', value: 90, label: '优' },
  { day: '五', value: 95, label: '优' },
  { day: '六', value: 83, label: '良' },
  { day: '日', value: 86, label: '良' }
]

// 每只宠物的本周健康趋势（联动首页切换）
export const petTrends = {
  mochi: [
    { day: '一', value: 92, label: '优' },
    { day: '二', value: 88, label: '良' },
    { day: '三', value: 74, label: '需关注' },
    { day: '四', value: 90, label: '优' },
    { day: '五', value: 95, label: '优' },
    { day: '六', value: 83, label: '良' },
    { day: '日', value: 86, label: '良' }
  ],
  doudou: [
    { day: '一', value: 80, label: '良' },
    { day: '二', value: 76, label: '需关注' },
    { day: '三', value: 84, label: '良' },
    { day: '四', value: 79, label: '需关注' },
    { day: '五', value: 88, label: '良' },
    { day: '六', value: 82, label: '良' },
    { day: '日', value: 90, label: '优' }
  ]
}

// 每只宠物的当日提醒（疫苗 / 驱虫 / 体检）
export const petReminders = {
  mochi: [
    { icon: 'calendar-check', label: '年度疫苗', date: '11-02', state: 'watch' },
    { icon: 'pill', label: '体内驱虫', date: '10-20', state: 'good' }
  ],
  doudou: [
    { icon: 'calendar-check', label: '狂犬疫苗', date: '10-22', state: 'watch' },
    { icon: 'scale', label: '体重复查', date: '10-15', state: 'good' }
  ]
}

// 每只宠物的体重历史（近 6 个月，kg）
export const petWeightHistory = {
  mochi: [
    { m: '5月', w: 4.1 },
    { m: '6月', w: 4.3 },
    { m: '7月', w: 4.4 },
    { m: '8月', w: 4.5 },
    { m: '9月', w: 4.6 },
    { m: '10月', w: 4.6 }
  ],
  doudou: [
    { m: '5月', w: 10.2 },
    { m: '6月', w: 10.6 },
    { m: '7月', w: 11.0 },
    { m: '8月', w: 11.3 },
    { m: '9月', w: 11.4 },
    { m: '10月', w: 11.2 }
  ]
}

// 每只宠物的免疫与护理日程
// type: vaccine 疫苗 / deworm 驱虫 / check 体检 / weight 称重 / groom 洗护 / other 自定义
// cycle: 展示用周期说明，便于用户理解为什么会有这条提醒
export const petSchedule = {
  mochi: [
    { id: 'm1', date: '2026-10-18', title: '体外驱虫', type: 'deworm', cycle: '每月一次' },
    { id: 'm2', date: '2026-10-20', title: '体内外驱虫', type: 'deworm', cycle: '每季度一次' },
    { id: 'm3', date: '2026-11-02', title: '年度疫苗（猫三联）', type: 'vaccine', cycle: '每年一次' },
    { id: 'm4', date: '2026-11-20', title: '口腔护理检查', type: 'check', cycle: '每半年一次' },
    { id: 'm5', date: '2026-09-12', title: '体态评估', type: 'check', cycle: '每半年一次' }
  ],
  doudou: [
    { id: 'd1', date: '2026-10-15', title: '体重复查', type: 'weight', cycle: '每月一次' },
    { id: 'd2', date: '2026-10-22', title: '狂犬疫苗加强', type: 'vaccine', cycle: '每年一次' },
    { id: 'd3', date: '2026-11-05', title: '洗澡与吹干护理', type: 'groom', cycle: '每月一次' },
    { id: 'd4', date: '2026-12-01', title: '髋关节影像复查', type: 'check', cycle: '每年一次' },
    { id: 'd5', date: '2026-08-03', title: '体内外驱虫', type: 'deworm', cycle: '每季度一次' }
  ]
}

// 日程类型元信息：图标、中文名与强调色
export const scheduleTypes = {
  vaccine: { label: '疫苗', icon: 'calendar-check', tone: 'coral' },
  deworm: { label: '驱虫', icon: 'pill', tone: 'sage' },
  check: { label: '体检', icon: 'stethoscope', tone: 'sand' },
  weight: { label: '称重', icon: 'scale', tone: 'peach' },
  groom: { label: '洗护', icon: 'sparkle', tone: 'sage' },
  other: { label: '自定义', icon: 'calendar', tone: 'ink' }
}

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

// 拍照识别：示例识别结果（接入 CV 模型后由后端返回）
export const recognitionSamples = [
  {
    id: 'r1',
    title: '英国短毛猫',
    sci: 'Felis catus',
    confidence: 0.96,
    species: 'cat',
    metrics: [
      { label: '品种匹配', value: '96%', state: 'good' },
      { label: '体态评估', value: '标准', state: 'good' },
      { label: '被毛状态', value: '光亮', state: 'good' },
      { label: '眼鼻检查', value: '正常', state: 'good' }
    ],
    note: '整体状态良好，被毛浓密有光泽，未见明显皮肤异常。'
  },
  {
    id: 'r2',
    title: '柯基犬',
    sci: 'Canis lupus',
    confidence: 0.93,
    species: 'dog',
    metrics: [
      { label: '品种匹配', value: '93%', state: 'good' },
      { label: '体态评估', value: '偏重', state: 'watch' },
      { label: '关节关注', value: '需注意', state: 'watch' },
      { label: '精神状况', value: '活跃', state: 'good' }
    ],
    note: '体重略高于标准区间，建议控制零食并增加散步；柯基需关注腰椎。'
  },
  {
    id: 'r3',
    title: '布偶猫',
    sci: 'Felis catus',
    confidence: 0.91,
    species: 'cat',
    metrics: [
      { label: '品种匹配', value: '91%', state: 'good' },
      { label: '被毛状态', value: '柔顺', state: 'good' },
      { label: '泪痕检查', value: '轻微', state: 'watch' },
      { label: '精神状态', value: '亲人', state: 'good' }
    ],
    note: '毛色与脸型符合布偶特征，被毛柔顺；泪痕略明显，可用湿巾每日清理。'
  }
]

// 品种百科：识别结果 → 知识入口（对接后端后替换为品种库接口）
export const breedLibrary = [
  {
    id: 'b-bsh',
    name: '英国短毛猫',
    sci: 'Felis catus',
    species: 'cat',
    origin: '英国',
    temperament: ['温和沉静', '独立不强求', '对陌生人有分寸'],
    weight: '4 – 7.5 kg',
    life: '12 – 15 年',
    issues: ['肥厚型心肌病', '肥胖倾向', '多囊肾（少见）'],
    care: '被毛短而致密，每周梳理 1–2 次即可；天性不爱运动，需要主人主动引导游戏，控制热量摄入以防发胖。'
  },
  {
    id: 'b-corgi',
    name: '柯基犬',
    sci: 'Canis lupus familiaris',
    species: 'dog',
    origin: '威尔士',
    temperament: ['机警聪明', '亲人爱凑热闹', '有牧牛执念爱追腿'],
    weight: '10 – 14 kg',
    life: '12 – 14 年',
    issues: ['椎间盘疾病（IVDD）', '髋关节发育不良', '肥胖加重腰椎负担'],
    care: '避免频繁上下楼梯与跳跃，控制体重是护腰第一要务；双层被毛换季大量掉毛，需每周多次梳理。'
  },
  {
    id: 'b-ragdoll',
    name: '布偶猫',
    sci: 'Felis catus',
    species: 'cat',
    origin: '美国加州',
    temperament: ['极度亲人', '忍耐力强', '被抱起时全身放松'],
    weight: '4.5 – 9 kg',
    life: '12 – 17 年',
    issues: ['肥厚型心肌病（基因筛查）', '泪痕', '毛球症'],
    care: '中长被毛需每日梳理防打结；浅色眼周易留泪痕，建议每日温水湿巾清洁；注意化毛膏或猫草辅助排毛。'
  },
  {
    id: 'b-golden',
    name: '金毛寻回犬',
    sci: 'Canis lupus familiaris',
    species: 'dog',
    origin: '苏格兰',
    temperament: ['温顺友善', '对人零戒心', '运动量需求大'],
    weight: '25 – 34 kg',
    life: '10 – 12 年',
    issues: ['髋/肘关节发育不良', '皮肤病（潮湿环境）', '耳道感染（垂耳）'],
    care: '每天保证 1 小时以上运动；洗澡后务必吹干被毛与耳道；大型犬幼年期控制生长速度，保护关节。'
  },
  {
    id: 'b-lihua',
    name: '中华田园猫',
    sci: 'Felis catus',
    species: 'cat',
    origin: '中国',
    temperament: ['适应力极强', '捕猎本能旺盛', '对主人忠诚但不粘人'],
    weight: '3.5 – 6 kg',
    life: '15 – 20 年',
    issues: ['总体遗传病少', '流浪期遗留寄生虫', '口腔结石'],
    care: '体质强健好养，注意定期驱虫与疫苗；成年后关注牙齿清洁，提供攀爬空间释放狩猎天性。'
  },
  {
    id: 'b-siamese',
    name: '暹罗猫',
    sci: 'Felis catus',
    species: 'cat',
    origin: '泰国',
    temperament: ['话痨爱交流', '精力旺盛', '认主人分离焦虑'],
    weight: '2.5 – 5 kg',
    life: '15 – 20 年',
    issues: ['呼吸道敏感', '分离焦虑', '进行性视网膜萎缩（基因筛查）'],
    care: '短毛易打理；每天需要大量互动与游戏；低温环境毛色会加深，冬季注意保暖。'
  }
]

// 智能问诊：初始对话（大模型接管后动态生成）
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

// 科室（医生筛选）
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

// 三种问诊方式（价格与说明）
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

// 医生库（演示数据，接入后端后由接口下发）
export const doctors = [
  {
    id: 'd1',
    name: '陈静',
    title: '主治医师',
    dept: 'internal',
    deptLabel: '犬猫内科',
    hospital: 'Petwise 合作动物医院 · 城西院区',
    years: 9,
    rating: 4.9,
    consults: 3240,
    online: true,
    responseMin: 6,
    tags: ['猫科消化', '呼吸道', '慢病管理'],
    good: ['猫传腹', '慢性呕吐', '软便腹泻'],
    intro: '专注猫科内科九年，擅长消化系统与慢性肾病的长程管理，主张「能不用药就不用药」。',
    certs: ['执业兽医师资格证', '中国畜牧兽医学会会员'],
    slot: '今日 14:00–22:00 可约',
    reviews: [
      { user: '橘座本座', rating: 5, text: '猫呕吐三天，医生问得很细，最后只是毛球，省了一趟医院。', time: '2 天前' },
      { user: '豆豆妈', rating: 5, text: '有耐心，把用药剂量写得清清楚楚，还提醒了复诊时间。', time: '5 天前' },
      { user: '阿黄', rating: 4, text: '回复稍慢一点，但建议很专业。', time: '1 周前' }
    ]
  },
  {
    id: 'd2',
    name: '王铮',
    title: '主任医师',
    dept: 'er',
    deptLabel: '急诊重症',
    hospital: 'Petwise 合作动物医院 · 24h 急诊中心',
    years: 14,
    rating: 4.8,
    consults: 1580,
    online: true,
    responseMin: 2,
    tags: ['急诊分诊', '中毒急救', '术后监护'],
    good: ['误食中毒', '呼吸困难', '急性呕吐'],
    intro: '急诊一线十四年，处理过大量误食异物、中暑与急性中毒病例，擅长快速判断是否需要立即线下就诊。',
    certs: ['执业兽医师资格证', '急诊急救专项认证'],
    slot: '全天候值班 · 平均 2 分钟响应',
    reviews: [
      { user: '小满', rating: 5, text: '半夜狗吃了巧克力，医生两分钟就回，指导催吐后送医，救回来了。', time: '3 天前' },
      { user: '柯基控', rating: 5, text: '判断很果断，直接告诉我该去急诊而不是观察。', time: '6 天前' }
    ]
  },
  {
    id: 'd3',
    name: '苏晴',
    title: '主治医师',
    dept: 'derma',
    deptLabel: '皮肤病',
    hospital: 'Petwise 合作动物医院 · 城中院区',
    years: 7,
    rating: 4.9,
    consults: 4820,
    online: true,
    responseMin: 9,
    tags: ['真菌感染', '过敏性皮炎', '耳道疾病'],
    good: ['反复挠耳', '脱毛斑秃', '皮肤红疹'],
    intro: '皮肤科方向，主张先用显微镜检查确诊再用药，反对盲目上激素。',
    certs: ['执业兽医师资格证', '皮肤病专科进修'],
    slot: '今日 10:00–20:00 可约',
    reviews: [
      { user: '麻薯妈', rating: 5, text: '拍照过去就看出是耳螨，用药一周就好了。', time: '1 天前' },
      { user: '雪球', rating: 5, text: '讲清楚了为什么会反复过敏，不是只开药。', time: '4 天前' }
    ]
  },
  {
    id: 'd4',
    name: '李维',
    title: '副主任医师',
    dept: 'surgery',
    deptLabel: '外科骨科',
    hospital: 'Petwise 合作动物医院 · 城西院区',
    years: 12,
    rating: 4.7,
    consults: 2110,
    online: false,
    responseMin: 25,
    tags: ['骨折固定', '软组织手术', '术后康复'],
    good: ['跛行', '伤口处理', '术后护理'],
    intro: '骨科与软组织外科，关注术后疼痛管理与康复训练方案的制定。',
    certs: ['执业兽医师资格证', '外科专科认证'],
    slot: '明日 09:00 起可约',
    reviews: [
      { user: '阿橘', rating: 5, text: '术后护理讲得很细，恢复得很好。', time: '2 周前' }
    ]
  },
  {
    id: 'd5',
    name: '林岚',
    title: '主治医师',
    dept: 'nutrition',
    deptLabel: '营养体重',
    hospital: 'Petwise 合作动物医院 · 线上门诊',
    years: 8,
    rating: 4.9,
    consults: 3960,
    online: true,
    responseMin: 12,
    tags: ['体重管理', '处方粮', '幼宠喂养'],
    good: ['肥胖', '挑食', '换粮腹泻'],
    intro: '营养方向，为超重宠物制定分阶段减重计划，反对一刀切断食。',
    certs: ['执业兽医师资格证', '宠物营养师认证'],
    slot: '今日 13:00–21:00 可约',
    reviews: [
      { user: '豆豆妈', rating: 5, text: '柯基减重两个月掉了 1.4kg，方案可执行。', time: '3 天前' }
    ]
  },
  {
    id: 'd6',
    name: '顾南',
    title: '主治医师',
    dept: 'exotic',
    deptLabel: '异宠专科',
    hospital: 'Petwise 合作动物医院 · 异宠中心',
    years: 6,
    rating: 4.6,
    consults: 890,
    online: false,
    responseMin: 40,
    tags: ['兔', '鸟', '爬行动物'],
    good: ['兔子胃肠停滞', '鹦鹉呼吸道', '龟壳问题'],
    intro: '异宠方向，接诊兔、鸟、爬行类，擅长解读异宠的隐匿症状。',
    certs: ['执业兽医师资格证', '异宠诊疗进修'],
    slot: '需预约 · 每周二四六',
    reviews: [
      { user: '兔几', rating: 5, text: '兔子不吃东西，医生一眼看出是胃肠停滞，处理很及时。', time: '1 周前' }
    ]
  },
  {
    id: 'd7',
    name: '周牧',
    title: '主治医师',
    dept: 'eye',
    deptLabel: '眼科',
    hospital: 'Petwise 合作动物医院 · 城中院区',
    years: 10,
    rating: 4.7,
    consults: 1640,
    online: true,
    responseMin: 15,
    tags: ['角膜溃疡', '白内障', '泪痕'],
    good: ['眼部分泌物', '眯眼流泪', '眼球发白'],
    intro: '眼科方向，配备裂隙灯与眼压检查，注重早期干预避免视力损伤。',
    certs: ['执业兽医师资格证', '眼科专项进修'],
    slot: '今日 15:00–21:00 可约',
    reviews: [{ user: '布偶控', rating: 5, text: '泪痕问题解决了，讲了日常清洁手法。', time: '5 天前' }]
  }
]

/* ============================================================
   结构化预问诊：部位 → 症状 → 时长 / 严重程度 / 伴随症状
   ============================================================ */

// 部位 → 症状（redFlag: true 为高危信号，命中即中断问卷并引导急诊）
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

// 持续时间（w = 分诊权重）
export const durations = [
  { id: 'today', label: '今天刚开始', w: 0 },
  { id: '2-3d', label: '2–3 天', w: 1 },
  { id: '1w', label: '约一周', w: 2 },
  { id: '1w+', label: '超过一周', w: 3 }
]

// 严重程度
export const severities = [
  { id: 'mild', label: '轻微 · 吃喝玩正常', w: 0 },
  { id: 'mid', label: '明显不适 · 但能进食', w: 2 },
  { id: 'severe', label: '精神差 · 不吃不喝', w: 4 }
]

// 伴随症状（多选，累加权重）
export const accompanyOptions = [
  { id: 'spirit', label: '精神萎靡', w: 3 },
  { id: 'appetite', label: '食欲下降', w: 3 },
  { id: 'fever', label: '身体发热 / 耳朵发烫', w: 2 },
  { id: 'vomit-ac', label: '呕吐', w: 2 },
  { id: 'diarrhea-ac', label: '腹泻', w: 2 },
  { id: 'drink-ac', label: '饮水异常', w: 1 },
  { id: 'sleep', label: '睡眠增多 / 躲藏', w: 1 }
]

// 症状快捷标签（按部位分组，点击即填入描述）
export const symptomGroups = [
  { group: '消化', items: ['呕吐', '软便腹泻', '食欲下降', '便秘'] },
  { group: '皮肤', items: ['频繁挠抓', '脱毛斑秃', '皮肤红疹', '皮屑增多'] },
  { group: '头颈', items: ['挠耳朵', '眼屎增多', '打喷嚏', '口臭流涎'] },
  { group: '全身', items: ['精神萎靡', '跛行', '体重骤变', '呼吸异常'] }
]

// AI 分诊规则：命中关键词 → 分级（emergency / urgent / home）
export const triageRules = [
  {
    level: 'emergency',
    keywords: ['呼吸困难', '张嘴呼吸', '抽搐', '癫痫', '大出血', '中毒', '巧克力', '误食', '难产', '骨折', '昏迷', '中暑', '尿不出来', '尿闭', '肚子胀硬', '车祸', '高空坠落'],
    label: '疑似急症',
    short: '建议立即线下急诊',
    advice: '这类情况线上问诊会延误治疗。请立即联系最近的 24 小时动物医院，途中保持宠物安静与体温。',
    actions: ['立即前往最近的急诊医院', '途中不要强行喂水喂食', '如为误食，带上包装或残留物']
  },
  {
    level: 'urgent',
    keywords: ['呕吐', '拉血', '带血', '拒食', '不吃不喝', '发热', '发烧', '跛行', '尿频', '尿血', '流脓', '肿大', '一直睡', '精神萎靡', '咳嗽'],
    label: '建议尽快就诊',
    short: '24 小时内预约医生',
    advice: '症状需要专业检查才能确诊。建议 24 小时内完成一次面诊或线上问诊，不要自行用药。',
    actions: ['记录症状开始时间与频次', '拍摄清晰照片或视频备用', '暂停自行给药，避免掩盖症状']
  },
  {
    level: 'home',
    keywords: ['掉毛', '梳毛', '皮屑', '轻微', '偶尔', '疫苗', '驱虫', '体重', '护理', '营养', '换粮'],
    label: '可先居家观察',
    short: '护理 + 观察 3 天',
    advice: '目前未见明确危险信号。可按建议居家护理并观察 3 天，若加重或出现新症状再就诊。',
    actions: ['按建议调整护理方式', '每日同一时间记录状态', '3 天未缓解则转为线上问诊']
  }
]

// 问诊记录（我的 → 问诊记录）
// type: ai 智能问诊 | human 真人问诊；state: closed 已完成 | pending 待医生回复 | reviewing 待评价
export const consultRecords = [
  {
    id: 'q1',
    date: '2026-10-09',
    petId: 'mochi',
    title: '软便两天但精神正常',
    preview: '精神食欲正常时可先观察，注意饮水与保暖；若持续 3 天以上或带血需就诊。',
    state: 'closed',
    type: 'ai',
    level: 'home'
  },
  {
    id: 'q2',
    date: '2026-10-08',
    petId: 'mochi',
    title: '反复挠右耳，耳道有褐色分泌物',
    preview: '考虑耳螨或真菌感染，医生已给出清洁步骤与用药建议，一周后复查。',
    state: 'closed',
    type: 'human',
    mode: 'text',
    doctorId: 'd3',
    level: 'urgent',
    rated: 5
  },
  {
    id: 'q3',
    date: '2026-10-10',
    petId: 'doudou',
    title: '昨晚呕吐一次，今晨精神尚可',
    preview: '已提交给王铮医生，等待接诊中。医生平均 2 分钟响应，请留意消息提醒。',
    state: 'pending',
    type: 'human',
    mode: 'video',
    doctorId: 'd2',
    level: 'urgent'
  },
  {
    id: 'q4',
    date: '2026-09-28',
    petId: 'doudou',
    title: '柯基体重是否超标',
    preview: '11.2kg 处于柯基正常区间上沿，建议控制零食并增加每日散步量。',
    state: 'closed',
    type: 'ai',
    level: 'home'
  },
  {
    id: 'q5',
    date: '2026-09-15',
    petId: 'mochi',
    title: '换季掉毛明显',
    preview: '每日梳毛 5 分钟促进血液循环，可减少毛球症；若出现斑秃需排查皮肤病。',
    state: 'closed',
    type: 'ai',
    level: 'home'
  }
]

// 我的收藏（品种百科 / 社区帖子 / 贴士）
export const favorites = [
  { id: 'f1', kind: 'breed', title: '英国短毛猫', desc: '温和沉静 · 寿命 12–15 年', to: '/breed/b-bsh' },
  { id: 'f2', kind: 'breed', title: '柯基犬', desc: '机警聪明 · 需关注腰椎', to: '/breed/b-corgi' },
  { id: 'f3', kind: 'post', title: '麻薯第一次跳上猫爬架顶端', desc: '阿橘的日常 · 128 赞', to: '/community' },
  { id: 'f4', kind: 'tip', title: '换季掉毛期护理', desc: '每日梳毛 5 分钟，减少毛球症', to: '/home' }
]

// 社区 / 朋友圈 feed
export const feed = [
  {
    id: 'p1',
    author: '阿橘的日常',
    species: 'cat',
    time: '12 分钟前',
    text: '麻薯今天第一次主动跳上猫爬架顶端，老母亲甚感欣慰。记录一下成长里程碑。',
    images: ['sage', 'peach', 'coral'],
    tags: ['#成长记录', '#英短'],
    likes: 128,
    comments: 23,
    liked: false
  },
  {
    id: 'p2',
    author: '柯基豆豆',
    species: 'dog',
    time: '1 小时前',
    text: '用 Petwise 拍了张照，识别说体态偏重哈哈，从今天开始遛弯加量！有没有同款胖柯基的家长？',
    images: ['peach', 'coral'],
    tags: ['#健康管理', '#柯基'],
    likes: 86,
    comments: 41,
    liked: true
  },
  {
    id: 'p3',
    author: '兽医老张',
    role: 'vet',
    time: '3 小时前',
    text: '换季提醒：猫咪出现频繁打喷嚏、流泪，先排查环境粉尘与温差，持续两天以上建议问诊。',
    images: [],
    tags: ['#科普', '#换季护理'],
    likes: 254,
    comments: 67,
    liked: false
  }
]

// 聊天会话列表
export const conversations = [
  {
    id: 'c1',
    name: '兽医老张',
    last: '麻薯的便便状态拍给我看看～',
    time: '09:30',
    unread: 2,
    online: true,
    kind: 'vet'
  },
  {
    id: 'c2',
    name: '橘座铲屎团',
    last: '周末线下撸猫局有人吗',
    time: '昨天',
    unread: 0,
    online: false,
    kind: 'group'
  },
  {
    id: 'c3',
    name: '豆豆的遛弯搭子',
    last: '明天公园见！',
    time: '周一',
    unread: 0,
    online: true,
    kind: 'friend'
  }
]

// 聊天详情（按会话 id 取）
export const chatRooms = {
  c1: [
    { role: 'them', text: '你好，麻薯最近状态怎么样？', time: '09:12' },
    { role: 'me', text: '昨天开始有点软便，今天好了一些', time: '09:14' },
    { role: 'them', text: '精神食欲正常的话可以先观察。便便成型了吗？', time: '09:16' },
    { role: 'me', text: '成型了，就是次数多一点', time: '09:20' },
    { role: 'them', text: '那问题不大，注意饮水和保暖。麻薯的便便状态拍给我看看～', time: '09:30' }
  ],
  c2: [
    { role: 'them', text: '周末线下撸猫局有人吗', time: '昨天' },
    { role: 'me', text: '我我我！地点定了吗', time: '昨天' }
  ],
  c3: [
    { role: 'them', text: '明天公园见！', time: '周一' },
    { role: 'me', text: '好嘞，带上飞盘', time: '周一' }
  ]
}

// 社区评论（按帖子 id 取，演示用）
export const commentsByPost = {
  p1: [
    { name: '豆豆妈', text: '太治愈了！同款英短飘过～', time: '8分钟前', liked: false },
    { name: '橘座铲屎团', text: '猫爬架顶端是勇者的证明', time: '5分钟前', liked: true },
    { name: '兽医老张', text: '运动量大说明状态不错，继续保持。', time: '3分钟前', liked: false }
  ],
  p2: [
    { name: '胖柯基联盟', text: '同款胖柯基+1，一起遛弯！', time: '40分钟前', liked: true },
    { name: '麻薯', text: '作为猫表示羡慕狗子的运动量哈哈', time: '20分钟前', liked: false }
  ],
  p3: [
    { name: '新手铲屎官', text: '收藏了，正好最近换季遇到这情况', time: '2小时前', liked: false },
    { name: '豆豆妈', text: '老张科普永远靠谱', time: '1小时前', liked: true }
  ]
}

// 发布时可选的内置"图片"色调（演示，接入后改为真实相册/相机）
export const galleryPool = ['sage', 'peach', 'ink', 'coral', 'sand', 'sage', 'peach', 'ink', 'coral', 'sand', 'sage', 'peach']

