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
export const petSchedule = {
  mochi: [
    { date: '2026-11-02', title: '年度疫苗（猫三联）', type: 'vaccine', state: 'watch' },
    { date: '2026-10-20', title: '体内外驱虫', type: 'deworm', state: 'good' },
    { date: '2026-09-12', title: '体态评估', type: 'check', state: 'good' }
  ],
  doudou: [
    { date: '2026-10-22', title: '狂犬疫苗加强', type: 'vaccine', state: 'watch' },
    { date: '2026-10-15', title: '体重复查', type: 'weight', state: 'good' },
    { date: '2026-08-03', title: '体内外驱虫', type: 'deworm', state: 'good' }
  ]
}

export const quickActions = [
  { id: 'scan', label: '拍照识别', sub: '品种 · 体态 · 状态', icon: 'camera', to: '/recognize', accent: true },
  { id: 'ask', label: '智能问诊', sub: 'AI 兽医在线', icon: 'stethoscope', to: '/consult' },
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

