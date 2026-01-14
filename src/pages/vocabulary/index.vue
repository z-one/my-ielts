<!-- eslint-disable eslint-comments/no-unlimited-disable -->
<script setup generic="T extends any, O extends any">
import vocabulary from './vocabulary'

const CHAPTER_KEY = 'vocabulary_chapter'
const PROGRESS_KEY = 'vocabulary_progress'
const CHAPTER_STATUS_KEY = 'vocabulary_chapter_status' // 章节学习状态
const MASTERY_COUNT = 10 // 正确10次后隐藏

// 章节学习状态枚举
const ChapterStatus = {
  NOT_LEARNED: 'not_learned',   // 未学习
  LEARNED: 'learned',           // 已学习
  COMPLETED: 'completed',        // 已完成
  MASTERED: 'mastered',          // 已熟练
}

const isTrainingModel = ref(false)
const isShowMeaning = ref(true)
const isAutoPlayWordAudio = ref(true)
const isOnlyShowErrors = ref(false)
const isFinishTraining = ref(false)
const isShowSource = ref(false)
const isHideMastered = ref(false)
const isShuffleMode = ref(false)
const isShowAddWordDialog = ref(false)
const showChapterStatusDialog = ref(false) // 显示章节状态设置对话框
const currentPage = ref(1)
const statusFilter = ref('all') // 状态筛选：all, not_learned, learned, completed, mastered
const chapterLearnStatus = ref({}) // 章节学习状态映射
const wordsPerPage = ref(Math.max(1, Number.parseInt(localStorage.getItem('vocabulary_words_per_page') || '5', 10))) // 每页显示组数，默认5组



const trainingStats = ref('')
const keyword = ref('')
const chapters = Object.keys(vocabulary)
const category = ref(localStorage.getItem(CHAPTER_KEY) || chapters[0])

const loaded = ref(false)
const refVocabulary = reactive(vocabulary)

// 获取当前显示的单词组
const currentWordGroups = computed(() => {
  const groups = refVocabulary[category.value]?.words || []

  // 如果是错词模式，返回所有错词扁平化后的数组
  if (isTrainingModel.value && isOnlyShowErrors.value) {
    const allErrorWords = []
    for (const group of groups) {
      const errorWords = group.filter(item => item.spellError)
      allErrorWords.push(errorWords)
    }
    return allErrorWords.length > 0 ? allErrorWords : [[]]
  }

  // 正常分页逻辑
  const start = (currentPage.value - 1) * wordsPerPage.value
  const end = start + wordsPerPage.value
  let pageGroups = groups.slice(start, end)

  // 如果开启打乱模式，打乱每组内部的单词顺序
  if (isShuffleMode.value) {
    pageGroups = pageGroups.map((group) => {
      const shuffledWords = [...group]
      for (let i = shuffledWords.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[shuffledWords[i], shuffledWords[j]] = [shuffledWords[j], shuffledWords[i]]
      }
      return shuffledWords
    })
  }

  return pageGroups
})

const totalPages = computed(() => {
  const groups = refVocabulary[category.value]?.words || []

  // 错词模式：所有错词作为一页
  if (isTrainingModel.value && isOnlyShowErrors.value)
    return 1

  // 正常模式：按组数计算
  return Math.ceil(groups.length / wordsPerPage.value)
})

// 章节学习状态：计算每个章节的学习进度
const chapterStatus = computed(() => {
  const status = {}
  for (const chapterName of chapters) {
    const chapter = refVocabulary[chapterName]
    if (!chapter || !chapter.words) {
      status[chapterName] = { progress: 0, mastered: 0, total: 0, label: chapterName }
      continue
    }

    let total = 0
    let mastered = 0

    for (const group of chapter.words) {
      for (const item of group) {
        total++
        if ((item.correctCount || 0) >= MASTERY_COUNT)
          mastered++
      }
    }

    const progress = total > 0 ? Math.round((mastered / total) * 100) : 0
    status[chapterName] = {
      progress,
      mastered,
      total,
      label: chapterName,
    }
  }
  return status
})

// 过滤后的章节列表
const filteredChapters = computed(() => {
  if (statusFilter.value === 'all')
    return chapters

  return chapters.filter(chapterName => {
    const status = chapterLearnStatus.value[chapterName] || ChapterStatus.NOT_LEARNED
    return status === statusFilter.value
  })
})

const wordList = computed(() => {
  const result = structuredClone(vocabulary) // deep clone
  // const keywordValue = keyword.value.trim().toLowerCase()
  const categoryValue = category.value

  if (categoryValue !== '') {
    // for (const key in result) {
    //   if (key !== categoryValue)
    //     delete result[key]
    // }
    return { [categoryValue]: result[categoryValue] }
  }

  /* if (keywordValue !== '') {
    for (const key in result) {
      const category = result[key]
      const words = []
      category.words.forEach((group) => {
        words.push(group.filter((item) => {
          return item.word.toLowerCase().includes(keywordValue)
        }))
      })
      category.words = words
    }
  } */
  return {}
})

watch(category, (newVal, oldVal) => {
  // console.log(newVal, oldVal)
  localStorage.setItem(CHAPTER_KEY, newVal)
})

// 保存练习进度
function saveProgress() {
  if (!isTrainingModel.value)
    return

  const progress = {
    chapter: category.value,
    words: {},
  }

  // 只保存练习状态
  const words = refVocabulary[category.value].words
  for (const group of words) {
    for (const item of group) {
      if (item.spellValue !== undefined || item.spellError !== undefined || item.correctCount !== undefined || item.errorCount !== undefined) {
        progress.words[item.id] = {
          spellValue: item.spellValue || '',
          spellError: item.spellError || false,
          correctCount: item.correctCount || 0,
          errorCount: item.errorCount || 0,
          showSource: item.showSource || false,
        }
      }
    }
  }

  localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress))
}

// 加载练习进度
function loadProgress() {
  const savedProgress = localStorage.getItem(PROGRESS_KEY)
  if (!savedProgress)
    return

  try {
    const progress = JSON.parse(savedProgress)
    if (progress.chapter !== category.value)
      return

    const words = refVocabulary[category.value].words
    for (const group of words) {
      for (const item of group) {
        const saved = progress.words[item.id]
        if (saved) {
          item.spellValue = saved.spellValue
          item.spellError = saved.spellError
          item.correctCount = saved.correctCount || 0
          item.errorCount = saved.errorCount || 0
          item.showSource = saved.showSource || false
        }
      }
    }

    trainingStats.value = calcStats()
  }
  catch (error) {
    console.error('加载进度失败:', error)
  }
}

// 保存章节学习状态
function saveChapterStatus() {
  localStorage.setItem(CHAPTER_STATUS_KEY, JSON.stringify(chapterLearnStatus.value))
}

// 加载章节学习状态
function loadChapterStatus() {
  const saved = localStorage.getItem(CHAPTER_STATUS_KEY)
  if (saved) {
    try {
      chapterLearnStatus.value = JSON.parse(saved)
    }
    catch (error) {
      console.error('加载章节状态失败:', error)
    }
  }
}

// 设置章节学习状态
function setChapterStatus(chapterName, status) {
  chapterLearnStatus.value[chapterName] = status
  saveChapterStatus()
}

// 获取章节状态文本
function getStatusText(status) {
  const statusMap = {
    [ChapterStatus.NOT_LEARNED]: '未学习',
    [ChapterStatus.LEARNED]: '已学习',
    [ChapterStatus.COMPLETED]: '已完成',
    [ChapterStatus.MASTERED]: '已熟练',
  }
  return statusMap[status] || '未学习'
}

// 获取章节状态图标
function getStatusIcon(status) {
  const iconMap = {
    [ChapterStatus.NOT_LEARNED]: '○',
    [ChapterStatus.LEARNED]: '◑',
    [ChapterStatus.COMPLETED]: '◐',
    [ChapterStatus.MASTERED]: '●',
  }
  return iconMap[status] || '○'
}

// 获取章节状态颜色类
function getStatusColorClass(status) {
  const colorMap = {
    [ChapterStatus.NOT_LEARNED]: 'text-gray-500',
    [ChapterStatus.LEARNED]: 'text-blue-500',
    [ChapterStatus.COMPLETED]: 'text-orange-500',
    [ChapterStatus.MASTERED]: 'text-green-500',
  }
  return colorMap[status] || 'text-gray-500'
}

// 获取章节下拉选项文本
function getChapterOptionText(chapterName) {
  const status = chapterLearnStatus.value[chapterName] || ChapterStatus.NOT_LEARNED
  return `${getStatusIcon(status)} ${chapterName} (${getStatusText(status)})`
}

// 获取章节下拉选项颜色类
function getChapterOptionClass(chapterName) {
  const status = chapterLearnStatus.value[chapterName] || ChapterStatus.NOT_LEARNED
  return getStatusColorClass(status)
}

function calcStats() {
  let error = 0
  let missing = 0
  let correct = 0
  let mastered = 0
  let totalCorrectCount = 0
  let totalErrorCount = 0

  if (isTrainingModel.value) {
    const cur = refVocabulary[category.value]
    // 遍历所有单词的属性
    for (const group of cur.words) {
      for (const item of group) {
        // 统计正确和错误次数
        totalCorrectCount += item.correctCount || 0
        totalErrorCount += item.errorCount || 0

        if (item.spellValue) {
          // eslint-disable-next-line max-statements-per-line
          if (item.spellError) { error++ }
          else {
            correct++
            if ((item.correctCount || 0) >= MASTERY_COUNT) {
              mastered++
            }
          }
        }
        else { missing++ }
      }
    }
  }
  return `${missing} 个未完成，${correct} 个正确，${error} 个错误，${mastered} 个已掌握 | 正确：${totalCorrectCount} 次，错误：${totalErrorCount} 次`
}

// 检测移动设备
const isMobile = ref(false)
const touchStartY = ref(0)
const touchEndY = ref(0)

onMounted(() => {
  loaded.value = true

  // 检测是否为移动设备
  const checkMobile = () => {
    isMobile.value = window.innerWidth <= 768
  }
  checkMobile()
  window.addEventListener('resize', checkMobile)

  // 初始化单词属性
  initWordProperties()

  // 初始化自添加生词
  initCustomWords()

  // 加载练习进度
  loadProgress()

  // 加载章节学习状态
  loadChapterStatus()

  // 只能同时播放一个音频
  const audioTags = document.getElementsByTagName('audio')
  for (const audio of audioTags) {
    audio.onplay = () => {
      for (const _audio of audioTags) {
        _audio.blur()
        if (audio !== _audio)
          _audio.pause()
      }
    }
  }

  // 移动端触摸事件处理
  if (isMobile.value) {
    document.addEventListener('touchstart', handleTouchStart, { passive: true })
    document.addEventListener('touchend', handleTouchEnd, { passive: true })
  }
})

onUnmounted(() => {
  // 清理工作
})

// 移动端触摸处理
function handleTouchStart(e) {
  touchStartY.value = e.touches[0].clientY
}

function handleTouchEnd(e) {
  touchEndY.value = e.changedTouches[0].clientY
  handleSwipe()
}

function handleSwipe() {
  const swipeDistance = touchStartY.value - touchEndY
  const minSwipeDistance = 50

  if (Math.abs(swipeDistance) < minSwipeDistance)
    return

  if (swipeDistance > 0) {
    // 向上滑动 - 下一页
    nextPage()
  }
  else {
    // 向下滑动 - 上一页
    prevPage()
  }
}

onUpdated(() => {
  // 音频再切换 SRC 之后需要调用一下 load() 不然看不到效果
  for (const el of document.getElementsByTagName('audio'))
    el.load()
})

// 移动端优化键盘事件处理
document.addEventListener('keydown', (ev) => {
  // 只在非移动端处理键盘事件
  if (isMobile.value)
    return

  // 激活的那个音频可以通过方向键进行快进/退
  if (['ArrowLeft', 'ArrowRight', ' '].includes(ev.key)) {
    ev.preventDefault()
    const audioTags = document.getElementsByTagName('audio')
    const keyMap = {
      ArrowLeft: -5,
      ArrowRight: 5,
    }
    for (const audioTag of audioTags) {
      audioTag.blur()
      if (keyMap[ev.key]) {
        const step = keyMap[ev.key]
        audioTag.currentTime = audioTag.currentTime + step
      }
      if (ev.key === ' ') {
        if (audioTag.paused)
          audioTag.play()
        else
          audioTag.pause()
      }
    }
  }
})

let audio = null
function play(audioPath) {
  if (audio) {
    audio.pause()
    audio.currentTime = 0
  }

  // 优化的音频播放，支持移动端和桌面端
  try {
    audio = new Audio()
    audio.src = audioPath
    audio.play().catch((error) => {
      console.log('音频播放失败:', error)
      // 移动端可能需要用户交互才能播放
      if (isMobile.value) {
        // 可以在这里显示提示，让用户点击播放
        // eslint-disable-next-line no-console
        console.log('移动端音频播放可能需要用户交互')
      }
    })
  }
  catch (error) {
    console.error('音频创建失败:', error)
  }
}



function copyText(item) {
  const text = `${item.word} ${item.pos} ${item.meaning}`
  navigator.clipboard.writeText(text)
}

function onInputKeydown(e) {
  e.stopPropagation()
  const { key, target } = e
  if (key === 'Enter') {
    // 触发验证（获取对应的item）
    const item = findItemById(target.id)
    if (item)
      validateInput(target, item)

    // 切换到下一个 input
    document.getElementById((Number(target.id) + 1).toString())?.focus()
  }
}

function onInputFoucsIn(e, audioPath) {
  if (isAutoPlayWordAudio.value)
    play(audioPath)

  // 自动朗读释义 - 简化版本
  if (isAutoPlayMeaningAudio.value) {
    const item = findItemById(e.target.id)
    if (item && item.meaning && item.id !== lastSpokenWordId.value) {
      // 防止重复朗读同一个单词
      lastSpokenWordId.value = item.id

      // 延迟一下，让单词音频先播放
      const delay = isAutoPlayWordAudio.value ? 2000 : 800
      setTimeout(() => {
        if (lastSpokenWordId.value === item.id) { // 确保还是同一个单词
          speakMeaning(item.meaning, item.word[0])
        }
      }, delay)
    }
  }
}

function onInputFoucsOut(e, item) {
  const { target } = e
  const spellValue = target.value.toLowerCase().trim()
  if (spellValue.length < 1) {
    item.spellValue = ''
  }
  else {
    const isCorrect = item.word.map(v => v.toLowerCase().trim()).includes(spellValue)
    item.spellValue = spellValue
    item.spellError = !isCorrect

    // 如果答对了，增加正确计数；如果答错了，增加错误计数
    if (isCorrect && !item.spellError)
      item.correctCount = (item.correctCount || 0) + 1
    else if (!isCorrect && item.spellError)
      item.errorCount = (item.errorCount || 0) + 1
  }
  trainingStats.value = calcStats()
  saveProgress() // 保存进度
}

function getInputStyleClass(item) {
  const cls = {
    error: 'w-full sm:w-auto ml-0 sm:ml-4 bg-red-50 border border-red-500 text-red-900 placeholder-red-700 text-sm rounded-lg focus:ring-red-500 dark:bg-gray-700 focus:border-red-500 inline-block p-2.5 dark:text-red-500 dark:placeholder-red-500 dark:border-red-500',
    normal: 'w-full sm:w-auto ml-0 sm:ml-4 inline-block border border-gray-300 rounded-lg bg-gray-50 p-2.5 text-sm text-gray-900 dark:border-gray-600 focus:border-blue-500 dark:bg-gray-700 dark:text-white focus:ring-blue-500 dark:focus:border-blue-500 dark:focus:ring-blue-500 dark:placeholder-gray-400',
    success: 'w-full sm:w-auto ml-0 sm:ml-4 bg-green-50 border border-green-500 text-green-900 dark:text-green-400 placeholder-green-700 dark:placeholder-green-500 text-sm rounded-lg focus:ring-green-500 focus:border-green-500 inline-block p-2.5 dark:bg-gray-700 dark:border-green-500',
  }
  // 在练习模式下，实时显示验证结果
  if (isTrainingModel.value) {
    if (item.spellError)
      return cls.error
    if (item.spellValue && item.spellValue.length > 0 && !item.spellError)
      return cls.success
  }
  // 完成练习后也显示结果
  if (isFinishTraining.value) {
    if (item.spellError)
      return cls.error
    if (item.spellValue && item.spellValue.length > 0 && !item.spellError)
      return cls.success
  }
  return cls.normal
}

function findItemById(id) {
  const words = refVocabulary[category.value].words
  for (const group of words) {
    for (const item of group) {
      if (item.id === id)
        return item
    }
  }
  return null
}

function validateInput(target, item) {
  const spellValue = target.value.toLowerCase().trim()
  if (spellValue.length < 1) {
    item.spellValue = ''
    item.spellError = false
  }
  else {
    const isCorrect = item.word.map(v => v.toLowerCase().trim()).includes(spellValue)
    item.spellValue = spellValue
    item.spellError = !isCorrect

    // 如果答对了，增加正确计数
    if (isCorrect && !item.spellError)
      item.correctCount = (item.correctCount || 0) + 1
  }
  trainingStats.value = calcStats()
  saveProgress() // 保存进度
}

function copyAllError() {
  const words = refVocabulary[category.value].words
  const errorWords = []
  for (const group of words) {
    for (const item of group) {
      if (item.spellError)
        errorWords.push(`${item.word} ${item.pos} ${item.meaning}`)
    }
  }
  navigator.clipboard.writeText(errorWords.join('\n\n'))
}

function shouldShowWord(item) {
  // 非练习模式：显示所有单词
  if (!isTrainingModel.value)
    return true

  // 练习模式下的过滤逻辑
  if (isOnlyShowErrors.value && !item.spellError)
    return false

  // 隐藏已掌握的单词（正确10次以上）
  if (isHideMastered.value && (item.correctCount || 0) >= MASTERY_COUNT)
    return false

  return true
}

function removeSingleWord(item) {
  if (!confirm(`确定要剔除单词"${item.word[0]}"吗？此操作不可恢复。`))
    return

  const words = refVocabulary[category.value].words

  // 查找并删除单词
  for (const group of words) {
    const index = group.findIndex(w => w.id === item.id)
    if (index > -1) {
      group.splice(index, 1)
      break
    }
  }

  // 更新章节统计
  const chapter = refVocabulary[category.value]
  chapter.groupCount = words.length
  chapter.wordCount = words.reduce((sum, group) => sum + group.length, 0)

  // 保存自添加生词章节的特殊处理
  if (category.value === '23 - 自添加生词')
    saveCustomWords()

  // 保存练习进度
  saveProgress()

  // 重新计算统计
  trainingStats.value = calcStats()

  // 如果这个组空了，且在只显示错误模式，可能需要关闭该模式
  if (words.some(group => group.length === 0)) {
    const hasAnyErrors = words.some(group =>
      group.some(item => item.spellError),
    )
    if (!hasAnyErrors)
      isOnlyShowErrors.value = false
  }

  alert(`已成功剔除单词"${item.word[0]}"`)
}

function removeErrorWords() {
  const confirmMessage = `确定要剔除当前章节的所有错词吗？
这些单词将被永久移除，此操作不可恢复。`
  if (!confirm(confirmMessage))
    return

  const words = refVocabulary[category.value].words
  const wordsToRemove = []

  // 收集所有错词
  for (const group of words) {
    for (const item of group) {
      if (item.spellError)
        wordsToRemove.push({ group, item })
    }
  }

  if (wordsToRemove.length === 0) {
    alert('当前没有错词需要剔除')
    return
  }

  // 从数组中移除错词
  for (const { group, item } of wordsToRemove) {
    const index = group.findIndex(w => w.id === item.id)
    if (index > -1)
      group.splice(index, 1)
  }

  // 更新章节统计
  const chapter = refVocabulary[category.value]
  chapter.groupCount = words.length
  chapter.wordCount = words.reduce((sum, group) => sum + group.length, 0)

  // 保存自添加生词章节的特殊处理
  if (category.value === '23 - 自添加生词')
    saveCustomWords()

  // 保存练习进度
  saveProgress()

  // 重新计算统计
  trainingStats.value = calcStats()

  // 关闭只显示错误模式
  isOnlyShowErrors.value = false

  alert(`已成功剔除 ${wordsToRemove.length} 个错词`)
}

function clearProgress() {
  // 清除当前章节的练习状态
  const words = refVocabulary[category.value].words
  for (const group of words) {
    for (const item of group) {
      item.spellValue = ''
      item.spellError = false
      item.correctCount = 0
      item.errorCount = 0
    }
  }

  // 清除本地存储
  localStorage.removeItem(PROGRESS_KEY)
  trainingStats.value = calcStats()
}

function goToPage(page) {
  if (page >= 1 && page <= totalPages.value)
    currentPage.value = page
}

function shuffleCurrentPage() {
  // 强制重新计算 currentWordGroups
  // eslint-disable-next-line no-unused-expressions
  currentWordGroups.value
}

function nextPage() {
  // eslint-disable-next-line curly
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

function prevPage() {
  // eslint-disable-next-line curly
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

function getVisiblePages() {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 7) {
    // 如果总页数少于等于7，显示所有页码
    for (let i = 1; i <= total; i++)
      pages.push(i)
  }
  else {
    // 显示当前页附近的页码
    if (current <= 3) {
      // 前3页的情况
      for (let i = 1; i <= 4; i++)
        pages.push(i)

      pages.push('...')
      pages.push(total)
    }
    else if (current >= total - 2) {
      // 最后3页的情况
      pages.push(1)
      pages.push('...')
      for (let i = total - 3; i <= total; i++)
        pages.push(i)
    }
    else {
      // 中间页的情况
      pages.push(1)
      pages.push('...')
      for (let i = current - 1; i <= current + 1; i++)
        pages.push(i)

      pages.push('...')
      pages.push(total)
    }
  }

  return pages
}

// 监听每页组数变化，保存到本地存储并重置页码
watch(wordsPerPage, (newValue) => {
  localStorage.setItem('vocabulary_words_per_page', newValue.toString())
  currentPage.value = 1 // 重置到第一页
})

// 监听每页组数变化，保存到本地存储并重置页码
watch(wordsPerPage, (newValue) => {
  localStorage.setItem('vocabulary_words_per_page', newValue.toString())
  currentPage.value = 1 // 重置到第一页
})

// 初始化单词属性
function initWordProperties() {
  for (const chapterKey in refVocabulary) {
    const chapter = refVocabulary[chapterKey]
    if (chapter.words) {
      for (const group of chapter.words) {
        for (const item of group) {
          if (item.showSource === undefined)
            item.showSource = false
        }
      }
    }
  }
}

// 初始化自添加生词章节
const CUSTOM_WORDS_KEY = 'vocabulary_custom_words'
function initCustomWords() {
  const customWords = localStorage.getItem(CUSTOM_WORDS_KEY)
  const defaultCustomWords = {
    groupCount: 0,
    wordCount: 0,
    audio: '',
    words: [],
  }

  if (customWords) {
    try {
      const parsed = JSON.parse(customWords)
      refVocabulary['23 - 自添加生词'] = {
        ...defaultCustomWords,
        ...parsed,
        groupCount: parsed.groupCount || 0,
        wordCount: parsed.wordCount || 0,
        words: parsed.words || [],
      }
    }
    catch (error) {
      console.error('加载自添加生词失败:', error)
      refVocabulary['23 - 自添加生词'] = defaultCustomWords
    }
  }
  else {
    refVocabulary['23 - 自添加生词'] = defaultCustomWords
  }

  // 初始化自定义单词的 showSource 属性
  const customChapter = refVocabulary['23 - 自添加生词']
  if (customChapter.words) {
    for (const group of customChapter.words) {
      for (const item of group) {
        if (item.showSource === undefined)
          item.showSource = false
      }
    }
  }
}

// 保存自添加生词
function saveCustomWords() {
  localStorage.setItem(CUSTOM_WORDS_KEY, JSON.stringify(refVocabulary['23 - 自添加生词']))
}

// 新添加单词的临时数据
const newWord = ref({
  word: '',
  pos: 'n.',
  meaning: '',
  example: '',
})

// 添加新单词
function addNewWord() {
  if (!newWord.value.word.trim() || !newWord.value.meaning.trim()) {
    alert('请填写单词和中文释义')
    return
  }

  const customWords = refVocabulary['23 - 自添加生词']
  if (!customWords)
    return

  const words = newWord.value.word.split(',').map(w => w.trim()).filter(w => w)

  if (words.length === 0)
    return

  // 创建新组或添加到现有组
  const groupName = `自定义组 ${(customWords.words?.length || 0) + 1}`
  const newGroup = words.map((word, index) => ({
    id: `custom_${Date.now()}_${index}`,
    word: [word],
    pos: newWord.value.pos || 'n.',
    meaning: newWord.value.meaning,
    example: newWord.value.example || '',
    extra: '',
    label: groupName,
  }))

  customWords.words = customWords.words || []
  customWords.words.push(newGroup)
  customWords.groupCount = customWords.words.length
  customWords.wordCount = customWords.words.reduce((sum, group) => sum + group.length, 0)

  // 重置表单
  newWord.value = {
    word: '',
    pos: 'n.',
    meaning: '',
    example: '',
  }

  saveCustomWords()
}

// 删除单词
function removeWord(groupIndex, wordIndex) {
  const customWords = refVocabulary['23 - 自添加生词']
  if (!customWords?.words?.[groupIndex])
    return

  customWords.words[groupIndex].splice(wordIndex, 1)

  // 如果组为空，删除整个组
  if (customWords.words[groupIndex].length === 0)
    customWords.words.splice(groupIndex, 1)

  customWords.groupCount = customWords.words.length
  customWords.wordCount = customWords.words.reduce((sum, group) => sum + group.length, 0)

  saveCustomWords()
}

// 删除整组
function removeGroup(groupIndex) {
  const customWords = refVocabulary['23 - 自添加生词']
  if (!customWords?.words)
    return

  customWords.words.splice(groupIndex, 1)

  customWords.groupCount = customWords.words.length
  customWords.wordCount = customWords.words.reduce((sum, group) => sum + group.length, 0)

  saveCustomWords()
}

// 清空所有自定义单词
function clearCustomWords() {
  if (confirm('确定要清空所有自添加的生词吗？此操作不可恢复。')) {
    refVocabulary['23 - 自添加生词'] = {
      groupCount: 0,
      wordCount: 0,
      audio: '',
      words: [],
    }
    saveCustomWords()
  }
}

// 切换章节时重置页码
watch(category, () => {
  currentPage.value = 1
})
</script>

<template>
  <div class="px-2 pt-4 lg:px-0 sm:px-4 sm:pt-6">
    <div class="p-3 shadow-sm mobile-card lg:p-6 sm:p-4">
      <!-- Card header -->
      <div class="mb-4 lg:mb-0">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 class="mb-1 text-lg font-bold text-gray-900 sm:text-xl dark:text-white">
              雅思词汇真经
            </h3>
            <span class="text-sm font-normal text-gray-500 sm:text-base dark:text-gray-400">涵盖雅思必备核心词，逻辑词群记忆法</span>
          </div>
        </div>
        <div class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <div class="flex flex-wrap items-center gap-2">
            <select
              v-model="category"
              class="block w-full text-sm mobile-input sm:flex-1"
            >
              <!-- <option value="">
                全部章节
              </option> -->
              <option v-for="k in filteredChapters" :key="k" :value="k" :class="getChapterOptionClass(k)">
                {{ getChapterOptionText(k) }}
              </option>
            </select>
            <!-- 状态筛选 -->
            <select
              v-model="statusFilter"
              class="block w-32 text-sm mobile-input"
            >
              <option value="all">全部</option>
              <option value="not_learned">未学习</option>
              <option value="learned">已学习</option>
              <option value="completed">已完成</option>
              <option value="mastered">已熟练</option>
            </select>
            <!-- 章节状态设置按钮 -->
            <button
              type="button"
              class="bg-purple-600 text-white mobile-button dark:bg-purple-500 hover:bg-purple-700 focus:ring-purple-300 dark:hover:bg-purple-600 dark:focus:ring-purple-800"
              @click="showChapterStatusDialog = true"
            >
              📚 标记章节
            </button>
            <button
              type="button"
              class="bg-indigo-600 text-white mobile-button dark:bg-indigo-500 hover:bg-indigo-700 focus:ring-indigo-300 dark:hover:bg-indigo-600 dark:focus:ring-indigo-800"
              @click="isShowAddWordDialog = true"
            >
              📝 添加生词
            </button>
            <label class="ml-2 inline-flex cursor-pointer items-center">
              <input v-model="isTrainingModel" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-blue-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-blue-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 text-sm font-medium text-blue-600 dark:text-blue-400">练习模式</span>
            </label>
            <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
              <input v-model="isShowMeaning" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-gray-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 text-sm font-medium text-gray-700 dark:text-gray-300">释义</span>
            </label>
            <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
              <input v-model="isShowSource" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-purple-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-purple-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 text-sm font-medium text-purple-600 dark:text-purple-400">原词</span>
            </label>

            <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
              <input v-model="isAutoPlayWordAudio" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-orange-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-orange-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 text-sm font-medium text-orange-600 dark:text-orange-400">自动播放</span>
            </label>
            <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
              <input v-model="isOnlyShowErrors" type="checkbox" class="peer sr-only" @change="currentPage = 1">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-red-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-red-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 text-sm font-medium text-red-600 dark:text-red-400">只显示错误</span>
            </label>
            <button
              v-if="isTrainingModel && isOnlyShowErrors"
              type="button"
              class="ml-2 rounded-lg bg-red-700 px-4 py-2.5 text-sm font-medium text-white dark:bg-red-600 hover:bg-red-800 focus:outline-none focus:ring-4 focus:ring-red-300 dark:hover:bg-red-700 dark:focus:ring-red-800"
              @click="removeErrorWords"
            >
              🗑️ 剔除错词
            </button>
            <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
              <input v-model="isHideMastered" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-green-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-green-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 text-sm font-medium text-green-600 dark:text-green-400">隐藏已掌握</span>
            </label>
            <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
              <input v-model="isShuffleMode" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-yellow-500 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-yellow-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-yellow-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 text-sm font-medium text-yellow-600 dark:text-yellow-400">打乱顺序</span>
            </label>
            <div class="ml-4 flex items-center">
              <span class="mr-2 text-sm font-medium text-gray-900 dark:text-gray-300">每组:</span>
              <select
                v-model="wordsPerPage"
                class="block w-20 border border-gray-300 rounded-lg bg-gray-50 p-2 text-sm text-gray-900 dark:border-gray-600 focus:border-blue-500 dark:bg-gray-700 dark:text-white focus:ring-blue-500 dark:focus:border-blue-500 dark:focus:ring-blue-500"
              >
                <option value="1">
                  1组
                </option>
                <option value="2">
                  2组
                </option>
                <option value="3">
                  3组
                </option>
                <option value="5">
                  5组
                </option>
                <option value="10">
                  10组
                </option>
                <option value="20">
                  20组
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>
      <!-- Table -->
      <div class="mt-4 flex flex-col sm:mt-6">
        <div class="overflow-x-auto rounded-lg">
          <div class="inline-block min-w-full align-middle">
            <div class="overflow-hidden shadow sm:rounded-lg">
              <!-- 移动端卡片视图 -->
              <div v-if="isMobile" class="space-y-3">
                <!-- 移动端章节信息 -->
                <div class="bg-gray-50 p-4 mobile-card dark:bg-gray-700">
                  <div class="flex flex-col space-y-3">
                    <div class="flex items-center justify-between">
                      <h4 class="text-lg font-semibold text-gray-900 dark:text-white">
                        {{ category }}
                      </h4>
                    </div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">
                      {{ refVocabulary[category]?.groupCount || 0 }} 组 {{ refVocabulary[category]?.wordCount || 0 }} 个词
                    </div>
                    <div v-if="totalPages > 1" class="text-sm text-gray-600 dark:text-gray-400">
                      第 {{ currentPage }} / {{ totalPages }} 组 (每页{{ wordsPerPage.value }}组)
                    </div>
                    <div v-if="refVocabulary[category]?.audio" class="flex justify-center">
                      <audio controls class="max-w-xs w-full">
                        <source :src="`vocabulary/audio/${refVocabulary[category].audio}`" type="audio/mpeg">
                      </audio>
                    </div>
                  </div>
                </div>
                <template v-for="(wordGroup, i) of currentWordGroups" :key="wordGroup.label">
                  <div
                    v-for="item of wordGroup"
                    v-show="shouldShowWord(item)"
                    :id="`tr_${item.id}`"
                    :key="item.id"
                    :class="{ [`group-color-${i % 15}`]: true }"
                    class="p-3 text-sm mobile-card"
                  >
                    <!-- 移动端卡片内容 -->
                    <div class="space-y-2">
                      <!-- 顶部操作栏 -->
                      <div class="flex items-center justify-between">
                        <span class="text-xs text-gray-500"># {{ item.id }}</span>
                        <div class="flex items-center gap-2">
                          <i
                            v-if="refVocabulary[category]?.audio"
                            class="i-ph-speaker-simple-high-bold text-blue-500"
                            @click="play(`vocabulary/audio/${category}/${item.word[0]}.mp3`)"
                          />

                          <template v-if="isTrainingModel">
                            <i
                              :class="`${item.showSource ? 'i-ph-eye-slash-bold' : 'i-ph-eye-bold'} text-gray-500`"
                              title="显示完整信息"
                              @click="item.showSource = !item.showSource"
                            />
                          </template>
                        </div>
                      </div>

                      <!-- 单词内容 -->
                      <div class="space-y-1">
                        <!-- 原词显示逻辑 -->
                        <div v-if="!isTrainingModel || item.showSource || isShowSource || (isTrainingModel && isOnlyShowErrors && item.spellError)">
                          <div class="font-medium text-gray-900 dark:text-white">
                            <span v-for="w in item.word" :key="w">
                              <a
                                class="text-blue-600 dark:text-blue-400 hover:underline"
                                :title="`在剑桥词典中查询 ${w}`"
                                target="_blank"
                                :href="`https://dictionary.cambridge.org/dictionary/english-chinese-simplified/${w}`"
                              >{{ w }}</a>
                            </span>
                            <span class="ml-2 text-sm italic text-gray-600 dark:text-gray-400">{{ item.pos }}</span>
                          </div>
                        </div>

                        <!-- 释义显示逻辑 -->
                        <div v-if="isShowMeaning || (isTrainingModel && item.showSource)" class="text-gray-700 dark:text-gray-300">
                          {{ item.meaning }}
                        </div>

                        <!-- 例句显示逻辑 -->
                        <div v-if="(!isTrainingModel && item.example) || (isTrainingModel && item.showSource && item.example)" class="text-xs text-gray-600 dark:text-gray-400">
                          {{ item.example }}
                        </div>

                        <!-- 拓展显示逻辑 -->
                        <div v-if="(!isTrainingModel && item.extra) || (isTrainingModel && item.showSource && item.extra)" class="text-xs text-gray-600 dark:text-gray-400">
                          {{ item.extra }}
                        </div>
                      </div>

                      <!-- 练习输入 -->
                      <template v-if="isTrainingModel">
                        <input
                          :id="item.id"
                          :class="getInputStyleClass(item)"
                          type="text"
                          placeholder="输入单词..."
                          autocomplete="off"
                          @focusout="onInputFoucsOut($event, item)"
                          @focusin="onInputFoucsIn($event, `vocabulary/audio/${category}/${item.word[0]}.mp3`)"
                          @keydown="onInputKeydown"
                        >

                        <!-- 统计信息 -->
                        <div v-if="isTrainingModel" class="flex items-center justify-between">
                          <div class="text-xs">
                            <span class="text-green-600 dark:text-green-400">✓ {{ item.correctCount || 0 }}</span>
                            <span class="ml-2 text-red-600 dark:text-red-400">✗ {{ item.errorCount || 0 }}</span>
                          </div>
                          <button
                            v-if="item.spellError"
                            type="button"
                            class="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white dark:bg-red-500 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 dark:hover:bg-red-600"
                            @click="removeSingleWord(item)"
                          >
                            剔除
                          </button>
                        </div>
                      </template>
                    </div>
                  </div>
                </template>
              </div>

              <!-- 桌面端表格视图 -->
              <table v-else class="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                <thead class="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      #
                    </th>
                    <th class="p-4 text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      <br>
                    </th>
                    <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      词
                    </th>
                    <th class="p-4 text-left text-xs font-medium text-gray-500 dark:text-white">
                      词性
                    </th>
                    <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      词义
                    </th>
                    <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      例句
                    </th>
                    <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      拓展
                    </th>
                    <th v-if="isTrainingModel" class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      统计
                    </th>
                    <th v-if="isTrainingModel" class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody v-if="!isMobile" class="bg-white dark:bg-gray-800">
                  <tr class="bg-hex-f3f3f3">
                    <td
                      :colspan="isTrainingModel ? 9 : 7"
                      class="px-4 py-6 text-sm font-normal text-gray-900 dark:bg-gray-500 dark:text-white"
                    >
                      <div class="flex flex-row">
                        <div class="flex flex-1 items-center">
                          <span class="text-lg">{{ category }}</span>
                          （ {{ refVocabulary[category]?.groupCount || 0 }} 组 {{ refVocabulary[category]?.wordCount || 0 }} 个词 ）
                          <span v-if="totalPages > 1" class="ml-4 text-sm text-gray-600">
                            第 {{ currentPage }} / {{ totalPages }} 组 (每页{{ wordsPerPage.value }}组)
                          </span>
                        </div>
                        <div v-if="refVocabulary[category]?.audio" class="justify-items-end">
                          <audio controls class="chapter">
                            <source :src="`vocabulary/audio/${refVocabulary[category].audio}`" type="audio/mpeg">
                          </audio>
                        </div>
                      </div>
                    </td>
                  </tr>
                  <template v-for="(wordGroup, i) of currentWordGroups" :key="wordGroup.label">
                    <tr
                      v-for="item of wordGroup"
                      v-show="shouldShowWord(item)" :id="`tr_${item.id}`"
                      :key="item.id"
                      :class="{ 'bg-gray-50 dark:bg-gray-700': item.id % 2 === 0, [`group-color-${i % 15}`]: true }" class="text-sm text-gray-900 dark:text-white"
                    >
                      <td class="p-4">
                        {{ item.id }}
                      </td>
                      <td>
                        <i
                          v-if="refVocabulary[category]?.audio"
                          class="i-ph-speaker-simple-high-bold inline-block cursor-pointer"
                          @click="play(`vocabulary/audio/${category}/${item.word[0]}.mp3`)"
                        />


                        <template v-if="isTrainingModel">
                          <i
                            :class="`${item.showSource ? 'i-ph-eye-slash-bold' : 'i-ph-eye-bold'} inline-block cursor-pointer ml-4`"
                            title="显示原词" @click="item.showSource = !item.showSource"
                          />
                          <input
                            :id="item.id" autocomplete="off" :class="getInputStyleClass(item)"
                            type="text"
                            @focusout="onInputFoucsOut($event, item)"
                            @focusin="onInputFoucsIn($event, `vocabulary/audio/${category}/${item.word[0]}.mp3`)"
                            @keydown="onInputKeydown"
                          >
                        </template>
                      </td>
                      <td class="group relative whitespace-nowrap p-4">
                        <div v-if="!isTrainingModel || item.showSource || isShowSource || (isTrainingModel && isOnlyShowErrors && item.spellError)">
                          <p v-for="w in item.word" :key="w">
                            <a
                              class="hover:underline" :title="`在剑桥词典中查询 ${w}`" target="_blank"
                              :href="`https://dictionary.cambridge.org/dictionary/english-chinese-simplified/${w}`"
                            >{{ w }}</a>
                          </p>

                          <div
                            class="absolute right-0 top-0 hidden h-100% items-center group-hover:flex"
                            @click="copyText(item)"
                          >
                            <i class="i-ph-copy block cursor-pointer px-4" />
                          </div>
                        </div>
                      </td>
                      <td style="font-style: italic; font-family: times;">
                        {{ item.pos }}
                      </td>
                      <td class="p-4">
                        {{ (isShowMeaning || (isTrainingModel && item.showSource)) ? item.meaning : '' }}
                      </td>
                      <td class="p-4">
                        {{ ((!isTrainingModel && item.example) || (isTrainingModel && item.showSource && item.example)) ? item.example : '' }}
                      </td>
                      <td class="p-4">
                        {{ ((!isTrainingModel && item.extra) || (isTrainingModel && item.showSource && item.extra)) ? item.extra : '' }}
                      </td>
                      <td v-if="isTrainingModel" class="p-4">
                        <div class="text-xs">
                          <span class="text-green-600 dark:text-green-400">
                            ✓ {{ item.correctCount || 0 }}
                          </span>
                          <span class="ml-2 text-red-600 dark:text-red-400">
                            ✗ {{ item.errorCount || 0 }}
                          </span>
                        </div>
                      </td>
                      <td v-if="isTrainingModel" class="p-4">
                        <button
                          v-if="item.spellError"
                          type="button"
                          class="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white dark:bg-red-500 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 dark:hover:bg-red-600"
                          @click="removeSingleWord(item)"
                        >
                          🗑️ 剔除
                        </button>
                        <span v-else class="text-xs text-gray-500 dark:text-gray-400">
                          -
                        </span>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页导航 -->
      <div v-if="totalPages > 1" class="mt-4 sm:mt-6">
        <!-- 移动端分页 -->
        <div v-if="isMobile" class="flex items-center justify-between">
          <button
            :disabled="currentPage === 1"
            class="flex-1 rounded-l-lg bg-blue-600 px-3 py-3 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            @click="prevPage"
          >
            ⬅️ 上一组
          </button>
          <div class="flex-1 bg-gray-100 px-4 py-3 text-center text-sm font-medium text-gray-700 dark:bg-gray-700 dark:text-gray-300">
            {{ currentPage }} / {{ totalPages }}
          </div>
          <button
            :disabled="currentPage === totalPages"
            class="flex-1 rounded-r-lg bg-blue-600 px-3 py-3 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            @click="nextPage"
          >
            下一组 ➡️
          </button>
        </div>

        <!-- 桌面端分页 -->
        <div v-else class="flex items-center justify-center space-x-2">
          <button
            :disabled="currentPage === 1"
            class="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed hover:bg-blue-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            @click="prevPage"
          >
            上一组
          </button>

          <div class="flex space-x-1">
            <button
              v-for="page in getVisiblePages()"
              :key="page"
              :class="{
                'bg-blue-600 text-white': currentPage === page,
                'bg-gray-200 text-gray-700 hover:bg-gray-300': currentPage !== page,
                'cursor-default': page === '...',
                'px-3 py-2 text-sm font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500': typeof page === 'number',
                'px-2 text-gray-500': page === '...',
              }"
              :disabled="page === '...'"
              @click="typeof page === 'number' ? goToPage(page) : null"
            >
              {{ page }}
            </button>
          </div>

          <button
            :disabled="currentPage === totalPages"
            class="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed hover:bg-blue-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            @click="nextPage"
          >
            下一组
          </button>
        </div>
      </div>

      <!-- Card Footer -->
      <div class="flex flex-col gap-4 pt-3 sm:pt-6">
        <div>
          <p v-if="isTrainingModel" class="text-sm text-gray-700 dark:text-gray-300">
            {{ trainingStats }}
          </p>
        </div>
        <div v-if="isTrainingModel">
          <!-- 移动端按钮网格 -->
          <div v-if="isMobile" class="grid grid-cols-2 gap-2 md:grid-cols-5 sm:grid-cols-3">
            <button
              type="button"
              class="bg-blue-700 text-white mobile-button dark:bg-blue-600 hover:bg-blue-800 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
              @click="isFinishTraining = true"
            >
              ✅ 完成练习
            </button>
            <button
              type="button"
              class="bg-blue-700 text-white mobile-button dark:bg-blue-600 hover:bg-blue-800 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
              @click="isOnlyShowErrors = !isOnlyShowErrors"
            >
              {{ isOnlyShowErrors ? '👁️ 展示所有' : '👁️ 仅错词' }}
            </button>
            <button
              type="button"
              class="bg-blue-700 text-white mobile-button dark:bg-blue-600 hover:bg-blue-800 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
              @click="copyAllError"
            >
              📋 拷贝错词
            </button>
            <button
              v-if="isShuffleMode"
              type="button"
              class="bg-yellow-600 text-white mobile-button dark:bg-yellow-500 hover:bg-yellow-700 focus:ring-yellow-300 dark:hover:bg-yellow-600 dark:focus:ring-yellow-800"
              @click="shuffleCurrentPage"
            >
              🔀 重新打乱
            </button>
            <button
              type="button"
              class="bg-red-700 text-white mobile-button dark:bg-red-600 hover:bg-red-800 focus:ring-red-300 dark:hover:bg-red-700 dark:focus:ring-red-800"
              @click="clearProgress"
            >
              🗑️ 清除进度
            </button>
          </div>
          <!-- 桌面端按钮行 -->
          <div v-else class="flex flex-wrap gap-2">
            <button
              type="button"
              class="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-medium text-white dark:bg-blue-600 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
              @click="isFinishTraining = true"
            >
              完成练习
            </button>
            <button
              type="button"
              class="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-medium text-white dark:bg-blue-600 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
              @click="isOnlyShowErrors = !isOnlyShowErrors"
            >
              {{ isOnlyShowErrors ? '展示所有' : '仅展示错词' }}
            </button>
            <button
              type="button"
              class="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-medium text-white dark:bg-blue-600 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
              @click="copyAllError"
            >
              拷贝错词
            </button>
            <button
              v-if="isShuffleMode"
              type="button"
              class="rounded-lg bg-yellow-600 px-5 py-2.5 text-sm font-medium text-white dark:bg-yellow-500 hover:bg-yellow-700 focus:outline-none focus:ring-4 focus:ring-yellow-300 dark:hover:bg-yellow-600 dark:focus:ring-yellow-800"
              @click="shuffleCurrentPage"
            >
              重新打乱
            </button>
            <button
              type="button"
              class="rounded-lg bg-red-700 px-5 py-2.5 text-sm font-medium text-white dark:bg-red-600 hover:bg-red-800 focus:outline-none focus:ring-4 focus:ring-red-300 dark:hover:bg-red-700 dark:focus:ring-red-800"
              @click="clearProgress"
            >
              清除进度
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 章节状态设置弹窗 -->
  <div v-if="showChapterStatusDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-2 sm:p-4">
    <div class="relative mx-auto max-h-[90vh] max-w-4xl w-full overflow-auto rounded-lg bg-white shadow-xl dark:bg-gray-800">
      <!-- 弹窗头部 -->
      <div class="sticky top-0 flex items-center justify-between border-b border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          📚 章节学习状态设置
        </h3>
        <button
          type="button"
          class="rounded-lg bg-transparent p-1.5 text-sm text-gray-400 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-700 dark:hover:text-white"
          @click="showChapterStatusDialog = false"
        >
          <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>

      <!-- 弹窗内容 -->
      <div class="p-6">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="chapterName in chapters"
            :key="chapterName"
            class="flex items-center justify-between rounded-lg border border-gray-200 p-4 dark:border-gray-600"
          >
            <div class="flex-1">
              <div class="font-medium text-gray-900 dark:text-white">
                {{ chapterName }}
              </div>
              <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                当前状态: <span :class="getStatusColorClass(chapterLearnStatus[chapterName])">{{ getStatusText(chapterLearnStatus[chapterName]) }}</span>
              </div>
            </div>
            <select
              :value="chapterLearnStatus[chapterName] || ChapterStatus.NOT_LEARNED"
              class="ml-4 block w-32 text-sm border border-gray-300 rounded-lg bg-gray-50 p-2 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
              @change="setChapterStatus(chapterName, $event.target.value)"
            >
              <option :value="ChapterStatus.NOT_LEARNED">未学习</option>
              <option :value="ChapterStatus.LEARNED">已学习</option>
              <option :value="ChapterStatus.COMPLETED">已完成</option>
              <option :value="ChapterStatus.MASTERED">已熟练</option>
            </select>
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="mt-6 rounded-lg bg-gray-50 p-4 dark:bg-gray-700">
          <h4 class="mb-3 text-lg font-medium text-gray-900 dark:text-white">
            学习进度统计
          </h4>
          <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-500 dark:text-gray-400">
                {{ Object.keys(chapterLearnStatus).filter(k => chapterLearnStatus[k] === ChapterStatus.NOT_LEARNED).length }}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">未学习</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-blue-500 dark:text-blue-400">
                {{ Object.keys(chapterLearnStatus).filter(k => chapterLearnStatus[k] === ChapterStatus.LEARNED).length }}
              </div>
              <div class="text-sm text-blue-600 dark:text-blue-400">已学习</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-orange-500 dark:text-orange-400">
                {{ Object.keys(chapterLearnStatus).filter(k => chapterLearnStatus[k] === ChapterStatus.COMPLETED).length }}
              </div>
              <div class="text-sm text-orange-600 dark:text-orange-400">已完成</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-green-500 dark:text-green-400">
                {{ Object.keys(chapterLearnStatus).filter(k => chapterLearnStatus[k] === ChapterStatus.MASTERED).length }}
              </div>
              <div class="text-sm text-green-600 dark:text-green-400">已熟练</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 添加生词弹窗 -->
  <div v-if="isShowAddWordDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-2 sm:p-4">
    <div class="relative mx-auto max-h-[90vh] max-w-2xl w-full overflow-auto rounded-lg bg-white shadow-xl dark:bg-gray-800">
      <!-- 弹窗头部 -->
      <div class="sticky top-0 flex items-center justify-between border-b border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          📝 添加生词管理
        </h3>
        <button
          type="button"
          class="rounded-lg bg-transparent p-1.5 text-sm text-gray-400 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-700 dark:hover:text-white"
          @click="isShowAddWordDialog = false"
        >
          <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>

      <!-- 弹窗内容 -->
      <div class="p-6">
        <!-- 快速添加表单 -->
        <div class="mb-6 rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
          <h4 class="mb-3 text-lg font-medium text-blue-900 dark:text-blue-100">
            快速添加单词
          </h4>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <input
              v-model="newWord.word"
              placeholder="单词（多个单词用逗号分隔）"
              class="mobile-input"
            >
            <input
              v-model="newWord.pos"
              placeholder="词性（如：n. v. adj.）"
              class="mobile-input"
            >
            <input
              v-model="newWord.meaning"
              placeholder="中文释义"
              class="sm:col-span-2 mobile-input"
            >
            <input
              v-model="newWord.example"
              placeholder="例句（可选）"
              class="sm:col-span-2 mobile-input"
            >
          </div>
          <div class="mt-4 flex justify-end">
            <button
              type="button"
              class="bg-blue-600 text-white mobile-button dark:bg-blue-500 hover:bg-blue-700 focus:ring-blue-300 dark:hover:bg-blue-600 dark:focus:ring-blue-800"
              @click="addNewWord"
            >
              ➕ 添加单词
            </button>
          </div>
        </div>

        <!-- 已添加的生词列表 -->
        <div class="rounded-lg bg-gray-50 p-4 dark:bg-gray-700">
          <div class="mb-4 flex items-center justify-between">
            <h4 class="text-lg font-medium text-gray-900 dark:text-white">
              已添加生词（{{ refVocabulary['23 - 自添加生词']?.wordCount || 0 }} 个）
            </h4>
            <button
              v-if="(refVocabulary['23 - 自添加生词']?.wordCount || 0) > 0"
              type="button"
              class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white dark:bg-red-500 hover:bg-red-700 focus:outline-none focus:ring-4 focus:ring-red-300 dark:hover:bg-red-600"
              @click="clearCustomWords"
            >
              🗑️ 清空所有
            </button>
          </div>

          <div class="max-h-96 overflow-auto">
            <div
              v-for="(group, groupIndex) in (refVocabulary['23 - 自添加生词']?.words || [])"
              :key="group.label"
              class="mb-4 border border-gray-200 rounded-lg bg-white p-4 dark:border-gray-600 dark:bg-gray-800"
            >
              <div class="mb-2 flex items-center justify-between">
                <h5 class="font-medium text-gray-900 dark:text-white">
                  {{ group.label }}
                </h5>
                <button
                  type="button"
                  class="rounded-lg bg-red-100 px-3 py-1 text-sm text-red-600 dark:bg-red-900/20 hover:bg-red-200 dark:text-red-400"
                  @click="removeGroup(groupIndex)"
                >
                  删除整组
                </button>
              </div>
              <div class="space-y-2">
                <div
                  v-for="(word, wordIndex) in group"
                  :key="word.id"
                  class="flex items-center justify-between border border-gray-200 rounded-lg p-3 dark:border-gray-600"
                >
                  <div class="flex-1">
                    <span class="font-medium text-gray-900 dark:text-white">{{ word.word }}</span>
                    <span class="ml-2 text-sm text-gray-600 dark:text-gray-400">({{ word.pos }})</span>
                    <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">{{ word.meaning }}</span>
                  </div>
                  <button
                    type="button"
                    class="rounded-lg bg-red-100 px-3 py-1 text-sm text-red-600 dark:bg-red-900/20 hover:bg-red-200 dark:text-red-400"
                    @click="removeWord(groupIndex, wordIndex)"
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
