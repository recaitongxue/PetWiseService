/**
 * 结构化预问诊 · 可解释分诊引擎
 * ------------------------------------------------------------------
 * 输入：向导收集到的结构化答案（部位 / 症状 / 时长 / 严重程度 / 伴随症状）
 * 输出：紧急度分级 + 评分 + 评分依据（factors）+ 可能原因 + 建议动作
 *
 * 设计要点：
 * 1) 高危信号（redFlag）一票否决，直接判为急症 —— 这类情况线上问诊会延误治疗
 * 2) 其余按加权评分，每个加分项都可回溯展示，避免"黑盒打分"
 * 3) 权重是规则常量，接入真实模型后可平滑替换为模型输出 + 规则兜底
 */
import { bodyParts, durations, severities, accompanyOptions, triageRules } from '@/data/mock'

// 症状 → 可能原因（兽医知识库片段，接入后端后由知识图谱下发）
const CAUSE_MAP = {
  'ear-itch': ['耳螨', '真菌感染', '外耳道炎', '食物或环境过敏'],
  'ear-discharge': ['耳螨', '细菌性外耳道炎', '马拉色菌感染'],
  'eye-discharge': ['结膜炎', '鼻泪管阻塞', '角膜损伤'],
  sneeze: ['上呼吸道感染', '过敏性鼻炎', '异物刺激'],
  mouth: ['牙结石与牙周炎', '口腔溃疡', '异物卡喉'],
  'head-tilt': ['前庭综合征', '中耳炎', '神经系统问题'],

  'skin-itch': ['跳蚤叮咬', '过敏性皮炎', '真菌感染'],
  'skin-loss': ['真菌感染', '蠕形螨', '内分泌异常', '过度舔舐'],
  'skin-rash': ['接触性皮炎', '细菌感染', '食物过敏'],
  'skin-lump': ['脂肪瘤', '脓肿', '乳腺或皮肤肿瘤'],
  'skin-lick': ['局部疼痛', '瘙痒性皮肤病', '心理性舔舐'],

  vomit: ['进食过快或饮食不当', '毛球症', '胃肠炎', '异物梗阻'],
  diarrhea: ['换粮应激', '肠道寄生虫', '食物不耐受', '细菌感染'],
  appetite: ['环境应激', '口腔或牙齿问题', '消化不适', '发热性疾病'],
  constipation: ['饮水不足', '毛球堵塞', '肠道动力不足'],
  'blood-stool': ['寄生虫感染', '结肠炎', '凝血异常'],

  cough: ['上呼吸道感染', '气管塌陷', '心脏问题', '过敏'],
  'breath-fast': ['呼吸道感染', '胸腔积液', '心脏疾病', '中暑'],
  'breath-open': ['呼吸道梗阻', '胸腔积液', '心脏病急性发作', '中暑'],
  pale: ['大出血', '休克', '严重贫血'],
  faint: ['心脏疾病', '低血糖', '严重贫血'],

  lame: ['软组织挫伤', '趾间炎', '关节扭伤', '骨折'],
  'no-jump': ['关节退行性病变', '脊椎问题', '肌肉拉伤'],
  joint: ['关节炎', '韧带损伤', '感染性关节炎'],
  paw: ['趾间炎', '异物刺入', '真菌感染'],
  paralysis: ['脊椎损伤', '血栓', '神经系统疾病'],

  'urine-freq': ['泌尿道感染', '膀胱结石', '糖尿病'],
  'urine-blood': ['泌尿道感染', '结石', '凝血功能障碍'],
  'urine-block': ['尿道栓子', '结石梗阻', '前列腺疾病'],
  drink: ['肾脏疾病', '糖尿病', '内分泌异常'],

  'spirit-low': ['感染性疾病', '疼痛', '代谢异常'],
  hide: ['疼痛或不适', '环境应激', '发热'],
  aggression: ['疼痛性防御', '神经系统问题', '甲状腺功能异常'],
  fit: ['癫痫', '低血糖', '中毒', '脑部病变'],

  'weight-loss': ['肠道寄生虫', '慢性肾病', '甲亢', '营养吸收不良'],
  'weight-gain': ['喂食过量', '运动不足', '内分泌异常'],
  poison: ['误食有毒食物', '化学物中毒', '药物过量'],
  trauma: ['骨折', '内出血', '软组织挫伤'],
  postop: ['术后正常恢复', '伤口感染', '缝线排异']
}

// 分诊阈值
const URGENT_THRESHOLD = 3

/** 取某部位下已选症状对象 */
function pickedSymptoms(partId, symptomIds) {
  const part = bodyParts.find((p) => p.id === partId)
  if (!part) return []
  return part.symptoms.filter((s) => symptomIds.includes(s.id))
}

export function scoreTriage(answers) {
  const { partId, symptomIds = [], durationId, severityId, accompanyIds = [] } = answers

  const duration = durations.find((d) => d.id === durationId)
  const severity = severities.find((s) => s.id === severityId)
  const symptoms = pickedSymptoms(partId, symptomIds)
  const accompany = accompanyOptions.filter((a) => accompanyIds.includes(a.id))

  const factors = []
  let score = 0

  /* ---- 1) 高危信号一票否决 ---- */
  const redFlags = symptoms.filter((s) => s.redFlag)
  if (redFlags.length) {
    factors.push({
      text: `高危信号：${redFlags.map((s) => s.label).join('、')}`,
      w: null,
      danger: true
    })
    return {
      level: 'emergency',
      score: 10,
      label: '疑似急症',
      short: '建议立即线下急诊',
      advice: triageRules[0].advice,
      causes: collectCauses(symptoms),
      actions: [
        ...triageRules[0].actions,
        '带上宠物与可能的致病原（包装、植物样本）'
      ],
      followUp: '请立即前往最近的 24 小时动物医院，途中保持宠物安静与体温稳定。',
      factors
    }
  }

  /* ---- 2) 加权评分 ---- */
  if (duration) {
    score += duration.w
    if (duration.w > 0) factors.push({ text: `已持续「${duration.label}」`, w: duration.w })
  }
  if (severity) {
    score += severity.w
    if (severity.w > 0) factors.push({ text: `严重程度「${severity.label}」`, w: severity.w })
  }
  symptoms.forEach((s) => {
    if (s.weight) {
      score += s.weight
      factors.push({ text: `症状加重项「${s.label}」`, w: s.weight })
    }
  })
  accompany.forEach((a) => {
    score += a.w
    factors.push({ text: `伴随「${a.label}」`, w: a.w })
  })

  const level = score >= URGENT_THRESHOLD ? 'urgent' : 'home'
  const rule = triageRules.find((r) => r.level === level)

  const actions = [...rule.actions]
  if (partId === 'skin') actions.push('每日同一光线角度拍一张患处照片，便于对比变化')
  if (partId === 'digest') actions.push('暂停零食与换粮，保留一份排泄物照片备用')
  if (partId === 'urinary') actions.push('记录每日排尿次数与尿量')

  return {
    level,
    score,
    label: rule.label,
    short: rule.short,
    advice: rule.advice,
    causes: collectCauses(symptoms, accompany),
    actions,
    followUp:
      level === 'urgent'
        ? '建议 24 小时内完成一次线上或线下面诊；用药 3 天无改善需复诊。'
        : '按建议居家护理并观察 3 天；若加重或出现新症状，随时转线上问诊。',
    factors
  }
}

function collectCauses(symptoms, accompany = []) {
  const out = []
  symptoms.forEach((s) => (CAUSE_MAP[s.id] || []).forEach((c) => out.push(c)))
  // 伴随症状中的特异性线索也并入
  if (accompany.some((a) => a.id === 'fever')) out.push('感染性发热')
  if (accompany.some((a) => a.id === 'vomit-ac')) out.push('胃肠道刺激')
  return [...new Set(out)].slice(0, 5)
}
