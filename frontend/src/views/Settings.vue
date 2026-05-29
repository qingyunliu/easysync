<template>
  <div class="settings-container">
    <div class="header">
      <h2>{{ $t('settings.pageTitle') }}</h2>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane :label="$t('settings.basicSettings')" name="basic">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>{{ $t('settings.basicSettings') }}</span>
            </div>
          </template>

          <el-form ref="basicFormRef" :model="settings" :rules="basicRules" label-width="180px">
            <el-form-item :label="$t('settings.maxConcurrentTasks')" prop="max_concurrent_tasks">
              <el-input-number v-model="settings.max_concurrent_tasks" :min="1" :max="20" />
              <div class="form-tip">{{ $t('settings.maxConcurrentTasksTip') }}</div>
            </el-form-item>

            <el-form-item :label="$t('settings.defaultRetryCount')" prop="default_retry_count">
              <el-input-number v-model="settings.default_retry_count" :min="0" :max="10" />
              <div class="form-tip">{{ $t('settings.defaultRetryCountTip') }}</div>
            </el-form-item>

            <el-form-item :label="$t('settings.defaultRetryDelay')" prop="default_retry_delay">
              <el-input-number v-model="settings.default_retry_delay" :min="1" :max="3600" />
              <div class="form-tip">{{ $t('settings.defaultRetryDelayTip') }}</div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSubmit">{{ $t('settings.saveSettings') }}</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('settings.logSettings')" name="logs">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>{{ $t('settings.logSettings') }}</span>
            </div>
          </template>

          <el-form ref="logsFormRef" :model="settings" :rules="logsRules" label-width="180px">
            <el-form-item :label="$t('settings.logRetentionDays')" prop="log_retention_days">
              <el-input-number v-model="settings.log_retention_days" :min="1" :max="365" />
              <div class="form-tip">{{ $t('settings.logRetentionDaysTip') }}</div>
            </el-form-item>

            <el-form-item :label="$t('settings.logLevel')" prop="log_level">
              <el-select v-model="settings.log_level">
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARNING" value="WARNING" />
                <el-option label="ERROR" value="ERROR" />
                <el-option label="CRITICAL" value="CRITICAL" />
              </el-select>
              <div class="form-tip">{{ $t('settings.logLevelTip') }}</div>
            </el-form-item>

            <el-form-item :label="$t('settings.logFilePath')" prop="log_file_path">
              <el-input v-model="settings.log_file_path" />
              <div class="form-tip">{{ $t('settings.logFilePathTip') }}</div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSubmit">{{ $t('settings.saveSettings') }}</el-button>
              <el-button @click="clearLogs">{{ $t('settings.clearLogs') }}</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="$t('settings.notificationSettings')" name="notifications">
        <div class="notify-section">
          <!-- 邮件通知分组 -->
          <div class="notify-group-title clickable" @click="toggleCollapse('email')">
            <span class="notify-bar email"></span>
            <el-icon>
              <Message />
            </el-icon>
            <span class="notify-title">{{ $t('settings.emailNotification') }}</span>
            <span class="flex-spacer"></span>
            <el-button v-if="!notifyStates.email.editing" type="link" @click.stop="startEdit('email')">{{
              $t('settings.edit')
              }}</el-button>
            <template v-else>
              <el-button type="primary" size="small" @click.stop="saveEdit('email')" :loading="saving"
                :disabled="!notifyStates.email.testPassed || saving">{{ $t('settings.save') }}</el-button>
              <el-button size="small" @click.stop="cancelEdit('email')">{{ $t('settings.cancel') }}</el-button>
            </template>
            <el-icon :class="notifyStates.email.collapsed ? 'collapse-arrow collapsed' : 'collapse-arrow'">
              <ArrowDown />
            </el-icon>
          </div>
          <div class="notify-switch-row">
            <el-switch v-model="settings.email_enabled" :disabled="!notifyStates.email.editing"
              :class="{ 'switch-disabled': !notifyStates.email.editing }" />
            <span class="notify-switch-label">{{ $t('settings.enableEmailNotification') }}</span>
          </div>
          <el-card v-show="!notifyStates.email.collapsed && settings.email_enabled">
            <el-form :model="settings" ref="emailForm" :rules="emailRules" label-width="120px" class="notify-form-col"
              :disabled="!notifyStates.email.editing">
              <el-form-item :label="$t('settings.smtpHost')" prop="smtp_host">
                <el-input v-model="settings.smtp_host" :placeholder="$t('settings.placeholders.smtpHost')" />
              </el-form-item>
              <el-form-item :label="$t('settings.smtpPort')" prop="smtp_port">
                <el-input-number v-model="settings.smtp_port" :min="1" :max="65535" style="width: 100%" />
              </el-form-item>
              <el-form-item :label="$t('settings.smtpUsername')" prop="smtp_username">
                <el-input v-model="settings.smtp_username" :placeholder="$t('settings.placeholders.username')" />
              </el-form-item>
              <el-form-item :label="$t('settings.smtpPassword')" prop="smtp_password">
                <el-input v-model="settings.smtp_password" type="password" show-password
                  :placeholder="$t('settings.placeholders.password')" />
              </el-form-item>
              <el-form-item :label="$t('settings.senderEmail')" prop="email">
                <el-input v-model="settings.email" :placeholder="$t('settings.placeholders.senderEmail')" />
              </el-form-item>
            </el-form>
            <div class="notify-actions-bar">
              <el-button @click="handleTest('email')" :disabled="saving">{{ $t('settings.testSend') }}</el-button>
            </div>
          </el-card>
          <!-- 短信通知分组 -->
          <div class="notify-group-title clickable" @click="toggleCollapse('sms')">
            <span class="notify-bar sms"></span>
            <el-icon>
              <Iphone />
            </el-icon>
            <span class="notify-title">{{ $t('settings.smsNotification') }}</span>
            <span class="flex-spacer"></span>
            <el-button v-if="!notifyStates.sms.editing" type="link" @click.stop="startEdit('sms')">{{
              $t('settings.edit')
              }}</el-button>
            <template v-else>
              <el-button type="primary" size="small" @click.stop="saveEdit('sms')" :loading="saving"
                :disabled="!notifyStates.sms.testPassed || saving">{{ $t('settings.save') }}</el-button>
              <el-button size="small" @click.stop="cancelEdit('sms')">{{ $t('settings.cancel') }}</el-button>
            </template>
            <el-icon :class="notifyStates.sms.collapsed ? 'collapse-arrow collapsed' : 'collapse-arrow'">
              <ArrowDown />
            </el-icon>
          </div>
          <div class="notify-switch-row">
            <el-switch v-model="settings.sms_enabled" :disabled="!notifyStates.sms.editing"
              :class="{ 'switch-disabled': !notifyStates.sms.editing }" />
            <span class="notify-switch-label">{{ $t('settings.enableSmsNotification') }}</span>
          </div>
          <el-card v-show="!notifyStates.sms.collapsed && settings.sms_enabled">
            <el-form :model="settings" ref="smsForm" :rules="smsRules" label-width="120px" class="notify-form-col"
              :disabled="!notifyStates.sms.editing">
              <el-form-item :label="$t('settings.smsProvider')" prop="sms_provider">
                <el-select v-model="settings.sms_provider" :placeholder="$t('settings.selectProvider')"
                  style="width: 100%">
                  <el-option :label="$t('settings.providers.aliyun')" value="aliyun" />
                  <el-option :label="$t('settings.providers.tencent')" value="tencent" />
                </el-select>
              </el-form-item>
              <el-form-item :label="$t('settings.smsApiKey')" prop="sms_api_key">
                <el-input v-model="settings.sms_api_key" type="password" show-password
                  :placeholder="$t('settings.placeholders.apiKey')" />
              </el-form-item>
              <el-form-item :label="$t('settings.smsTemplateId')" prop="sms_template_id">
                <el-input v-model="settings.sms_template_id" :placeholder="$t('settings.placeholders.smsTemplateId')" />
              </el-form-item>
              <el-form-item :label="$t('settings.smsSignName')" prop="sms_sign_name">
                <el-input v-model="settings.sms_sign_name" :placeholder="$t('settings.placeholders.smsSignName')" />
              </el-form-item>
            </el-form>
            <div class="notify-actions-bar">
              <el-button @click="handleTest('sms')" :disabled="saving">{{ $t('settings.testSend') }}</el-button>
            </div>
          </el-card>
          <!-- 钉钉通知分组 -->
          <div class="notify-group-title clickable" @click="toggleCollapse('dingtalk')">
            <span class="notify-bar dingtalk"></span>
            <el-icon>
              <ChatDotRound />
            </el-icon>
            <span class="notify-title">{{ $t('settings.dingtalkNotification') }}</span>
            <span class="flex-spacer"></span>
            <el-button v-if="!notifyStates.dingtalk.editing" type="link" @click.stop="startEdit('dingtalk')">{{
              $t('settings.edit') }}</el-button>
            <template v-else>
              <el-button type="primary" size="small" @click.stop="saveEdit('dingtalk')" :loading="saving"
                :disabled="!notifyStates.dingtalk.testPassed || saving">{{ $t('settings.save') }}</el-button>
              <el-button size="small" @click.stop="cancelEdit('dingtalk')">{{ $t('settings.cancel') }}</el-button>
            </template>
            <el-icon :class="notifyStates.dingtalk.collapsed ? 'collapse-arrow collapsed' : 'collapse-arrow'">
              <ArrowDown />
            </el-icon>
          </div>
          <div class="notify-switch-row">
            <el-switch v-model="settings.dingtalk_enabled" :disabled="!notifyStates.dingtalk.editing"
              :class="{ 'switch-disabled': !notifyStates.dingtalk.editing }" />
            <span class="notify-switch-label">{{ $t('settings.enableDingtalkNotification') }}</span>
          </div>
          <el-card v-show="!notifyStates.dingtalk.collapsed && settings.dingtalk_enabled">
            <el-form :model="settings" ref="dingtalkForm" :rules="dingtalkRules" label-width="120px"
              class="notify-form-col" :disabled="!notifyStates.dingtalk.editing">
              <el-form-item :label="$t('settings.dingtalkWebhook')" prop="dingtalk_webhook">
                <el-input v-model="settings.dingtalk_webhook"
                  :placeholder="$t('settings.placeholders.dingtalkWebhook')" />
              </el-form-item>
              <el-form-item :label="$t('settings.dingtalkSecret')" prop="dingtalk_secret">
                <el-input v-model="settings.dingtalk_secret" type="password" show-password
                  :placeholder="$t('settings.placeholders.dingtalkSecret')" />
              </el-form-item>
            </el-form>
            <div class="notify-actions-bar">
              <el-button @click="handleTest('dingtalk')" :disabled="saving">{{ $t('settings.testSend') }}</el-button>
            </div>
          </el-card>
          <!-- Webhook通知分组 -->
          <div class="notify-group-title clickable" @click="toggleCollapse('webhook')">
            <span class="notify-bar webhook"></span>
            <el-icon>
              <Link />
            </el-icon>
            <span class="notify-title">{{ $t('settings.webhookNotification') }}</span>
            <span class="flex-spacer"></span>
            <el-button v-if="!notifyStates.webhook.editing" type="link" @click.stop="startEdit('webhook')">{{
              $t('settings.edit') }}</el-button>
            <template v-else>
              <el-button type="primary" size="small" @click.stop="saveEdit('webhook')" :loading="saving"
                :disabled="!notifyStates.webhook.testPassed || saving">{{ $t('settings.save') }}</el-button>
              <el-button size="small" @click.stop="cancelEdit('webhook')">{{ $t('settings.cancel') }}</el-button>
            </template>
            <el-icon :class="notifyStates.webhook.collapsed ? 'collapse-arrow collapsed' : 'collapse-arrow'">
              <ArrowDown />
            </el-icon>
          </div>
          <div class="notify-switch-row">
            <el-switch v-model="settings.webhook_enabled" :disabled="!notifyStates.webhook.editing"
              :class="{ 'switch-disabled': !notifyStates.webhook.editing }" />
            <span class="notify-switch-label">{{ $t('settings.enableWebhookNotification') }}</span>
          </div>
          <el-card v-show="!notifyStates.webhook.collapsed && settings.webhook_enabled">
            <el-form :model="settings" ref="webhookForm" :rules="webhookRules" label-width="120px"
              class="notify-form-col" :disabled="!notifyStates.webhook.editing">
              <el-form-item :label="$t('settings.webhookUrl')" prop="webhook_url">
                <el-input v-model="settings.webhook_url" :placeholder="$t('settings.placeholders.webhookUrl')" />
              </el-form-item>
              <el-form-item :label="$t('settings.webhookSecret')" prop="webhook_secret">
                <el-input v-model="settings.webhook_secret" type="password" show-password
                  :placeholder="$t('settings.placeholders.webhookSecret')" />
              </el-form-item>
            </el-form>
            <div class="notify-actions-bar">
              <el-button @click="handleTest('webhook')" :disabled="saving">{{ $t('settings.testSend') }}</el-button>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Switch,
  Message,
  Link,
  ChatDotRound,
  Iphone,
  Bell,
  ArrowDown
} from '@element-plus/icons-vue'
import axios from '@/utils/axios.mjs'

const { t } = useI18n()

// 新增表单ref和数据
const basicFormRef = ref(null)
const logsFormRef = ref(null)

const activeTab = ref('basic')
const saving = ref(false)
const testing = ref(false)

// 折叠与编辑状态
const notifyStates = reactive({
  email: { collapsed: false, editing: false, backup: {}, testPassed: false },
  sms: { collapsed: false, editing: false, backup: {}, testPassed: false },
  dingtalk: { collapsed: false, editing: false, backup: {}, testPassed: false },
  webhook: { collapsed: false, editing: false, backup: {}, testPassed: false }
})

function toggleCollapse(type) {
  notifyStates[type].collapsed = !notifyStates[type].collapsed
}
function startEdit(type) {
  notifyStates[type].editing = true
  notifyStates[type].testPassed = false
  // 备份当前配置
  notifyStates[type].backup = JSON.parse(JSON.stringify(settings.value))
}
function cancelEdit(type) {
  ElMessageBox.confirm(t('settings.messages.confirmCancelEdit'), t('settings.messages.confirmCancel'), {
    confirmButtonText: t('settings.confirm'),
    cancelButtonText: t('settings.continueEdit'),
    type: 'warning',
  }).then(() => {
    // 还原备份
    Object.assign(settings.value, notifyStates[type].backup)
    notifyStates[type].editing = false
    notifyStates[type].testPassed = false
  }).catch(() => {
    // 用户点击“继续编辑”，无需处理
  })
}
async function saveEdit(type) {
  // 只校验当前分组
  let formRef = null
  if (type === 'email') formRef = emailForm
  if (type === 'sms') formRef = smsForm
  if (type === 'dingtalk') formRef = dingtalkForm
  if (type === 'webhook') formRef = webhookForm
  if (!formRef.value) return
  formRef.value.validate(async (valid) => {
    if (!valid) return
    if (!notifyStates[type].testPassed) {
      ElMessage.warning(t('settings.messages.testFirstThenSave'))
      return
    }
    saving.value = true
    try {
      await axios.put('/settings', settings.value)
      ElMessage.success(t('settings.messages.settingsSaved'))
      notifyStates[type].editing = false
      notifyStates[type].testPassed = false
    } catch (error) {
      ElMessage.error(t('settings.messages.saveNotificationSettingsFailed'))
    } finally {
      saving.value = false
    }
  })
}

// 统一 settings 对象，包含所有设置
const settings = ref({
  // 基本设置
  max_concurrent_tasks: 5,
  default_retry_count: 3,
  default_retry_delay: 60,
  // 日志设置
  log_retention_days: 30,
  log_level: 'INFO',
  log_file_path: '',
  // 通知设置
  enabled: false,
  email_enabled: false,
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  email: '',
  webhook_enabled: false,
  webhook_url: '',
  webhook_secret: '',
  dingtalk_enabled: false,
  dingtalk_webhook: '',
  dingtalk_secret: '',
  sms_enabled: false,
  sms_provider: '',
  sms_api_key: '',
  sms_template_id: '',
  sms_sign_name: '',
  // 通知事件
  event_scan_success: true,
  event_scan_error: true
})

const basicRules = {
  max_concurrent_tasks: [
    { required: true, message: t('settings.validation.enterMaxConcurrentTasks'), trigger: 'blur' }
  ],
  default_retry_count: [
    { required: true, message: t('settings.validation.enterDefaultRetryCount'), trigger: 'blur' }
  ],
  default_retry_delay: [
    { required: true, message: t('settings.validation.enterDefaultRetryDelay'), trigger: 'blur' }
  ]
}

const logsRules = {
  log_retention_days: [
    { required: true, message: t('settings.validation.enterLogRetentionDays'), trigger: 'blur' }
  ],
  log_level: [
    { required: true, message: t('settings.validation.selectLogLevel'), trigger: 'change' }
  ],
  log_file_path: [
    { required: true, message: t('settings.validation.enterLogFilePath'), trigger: 'blur' }
  ]
}

const emailForm = ref(null)
const webhookForm = ref(null)
const dingtalkForm = ref(null)
const smsForm = ref(null)

const emailRules = {
  email: [
    { required: true, message: t('settings.validation.enterEmailAddress'), trigger: 'blur' },
    { type: 'email', message: t('settings.validation.enterValidEmailFormat'), trigger: 'blur' }
  ],
  smtp_host: [
    { required: true, message: t('settings.validation.enterSmtpHost'), trigger: 'blur' }
  ],
  smtp_port: [
    { required: true, message: t('settings.validation.enterSmtpPort'), trigger: 'blur' }
  ],
  smtp_username: [
    { required: true, message: t('settings.validation.enterSmtpUsername'), trigger: 'blur' }
  ],
  smtp_password: [
    { required: true, message: t('settings.validation.enterSmtpPassword'), trigger: 'blur' }
  ]
}

const webhookRules = {
  webhook_url: [
    { required: true, message: t('settings.validation.enterWebhookUrl'), trigger: 'blur' },
    { type: 'url', message: t('settings.validation.enterValidUrlFormat'), trigger: 'blur' }
  ],
  webhook_secret: [
    { required: true, message: t('settings.validation.enterWebhookSecret'), trigger: 'blur' }
  ]
}

const dingtalkRules = {
  dingtalk_webhook: [
    { required: true, message: t('settings.validation.enterDingtalkWebhook'), trigger: 'blur' },
    { type: 'url', message: t('settings.validation.enterValidUrlFormat'), trigger: 'blur' }
  ],
  dingtalk_secret: [
    { required: true, message: t('settings.validation.enterDingtalkSecret'), trigger: 'blur' }
  ]
}

const smsRules = {
  sms_provider: [
    { required: true, message: t('settings.validation.selectSmsProvider'), trigger: 'change' }
  ],
  sms_api_key: [
    { required: true, message: t('settings.validation.enterApiKey'), trigger: 'blur' }
  ],
  sms_template_id: [
    { required: true, message: t('settings.validation.enterTemplateId'), trigger: 'blur' }
  ],
  sms_sign_name: [
    { required: true, message: t('settings.validation.enterSignName'), trigger: 'blur' }
  ]
}

const notifyForm = ref(null)
const notifyRules = computed(() => {
  const rules = {}
  if (settings.value.email_enabled) {
    rules.email = [
      { required: true, message: t('settings.validation.enterEmailAddress'), trigger: 'blur' },
      { type: 'email', message: t('settings.validation.enterValidEmailFormat'), trigger: 'blur' }
    ]
    rules.smtp_host = [
      { required: true, message: t('settings.validation.enterSmtpHost'), trigger: 'blur' }
    ]
    rules.smtp_port = [
      { required: true, message: t('settings.validation.enterSmtpPort'), trigger: 'blur' }
    ]
    rules.smtp_username = [
      { required: true, message: t('settings.validation.enterSmtpUsername'), trigger: 'blur' }
    ]
    rules.smtp_password = [
      { required: true, message: t('settings.validation.enterSmtpPassword'), trigger: 'blur' }
    ]
  }
  if (settings.value.webhook_enabled) {
    rules.webhook_url = [
      { required: true, message: t('settings.validation.enterWebhookUrl'), trigger: 'blur' },
      { type: 'url', message: t('settings.validation.enterValidUrlFormat'), trigger: 'blur' }
    ]
  }
  if (settings.value.dingtalk_enabled) {
    rules.dingtalk_webhook = [
      { required: true, message: t('settings.validation.enterDingtalkWebhook'), trigger: 'blur' },
      { type: 'url', message: t('settings.validation.enterValidUrlFormat'), trigger: 'blur' }
    ]
  }
  if (settings.value.sms_enabled) {
    rules.sms_provider = [
      { required: true, message: t('settings.validation.selectProvider'), trigger: 'change' }
    ]
    rules.sms_api_key = [
      { required: true, message: t('settings.validation.enterApiKey'), trigger: 'blur' }
    ]
    rules.sms_template_id = [
      { required: true, message: t('settings.validation.enterTemplateId'), trigger: 'blur' }
    ]
    rules.sms_sign_name = [
      { required: true, message: t('settings.validation.enterSignName'), trigger: 'blur' }
    ]
  }
  return rules
})

const fetchSettings = async () => {
  try {
    const response = await axios.get('/settings')
    const data = response.data.data
    Object.assign(settings.value, data)
  } catch (error) {
    ElMessage.error(t('settings.messages.getSystemSettingsFailed'))
  }
}

const handleSubmit = async () => {
  try {
    saving.value = true
    await axios.put('/settings', settings.value)
    ElMessage.success(t('settings.messages.settingsSaved'))
  } catch (error) {
    ElMessage.error(t('settings.messages.saveSettingsFailed'))
  } finally {
    saving.value = false
  }
}

function handleTest(type) {
  let formRef = null
  if (type === 'email') formRef = emailForm
  if (type === 'sms') formRef = smsForm
  if (type === 'dingtalk') formRef = dingtalkForm
  if (type === 'webhook') formRef = webhookForm
  if (!formRef.value) return
  formRef.value.validate(async (valid) => {
    if (!valid) return
    testing.value = true
    // 只传当前分组的配置
    const config = { type }
    if (type === 'email') {
      config.email_enabled = settings.value.email_enabled
      config.smtp_host = settings.value.smtp_host
      config.smtp_port = settings.value.smtp_port
      config.smtp_username = settings.value.smtp_username
      config.smtp_password = settings.value.smtp_password
      config.email = settings.value.email
    }
    if (type === 'sms') {
      config.sms_enabled = settings.value.sms_enabled
      config.sms_provider = settings.value.sms_provider
      config.sms_api_key = settings.value.sms_api_key
      config.sms_template_id = settings.value.sms_template_id
      config.sms_sign_name = settings.value.sms_sign_name
    }
    if (type === 'dingtalk') {
      config.dingtalk_enabled = settings.value.dingtalk_enabled
      config.dingtalk_webhook = settings.value.dingtalk_webhook
      config.dingtalk_secret = settings.value.dingtalk_secret
    }
    if (type === 'webhook') {
      config.webhook_enabled = settings.value.webhook_enabled
      config.webhook_url = settings.value.webhook_url
      config.webhook_secret = settings.value.webhook_secret
    }
    axios.post('/notifications/test', config)
      .then(() => {
        ElMessage.success(t('settings.messages.testNotificationSent'))
        notifyStates[type].testPassed = true
      })
      .catch(error => {
        ElMessage.error(error.response?.data?.message || error.response?.data?.msg || t('settings.messages.testNotificationFailed'))
        notifyStates[type].testPassed = false
      })
      .finally(() => {
        testing.value = false
      })
  })
}

const handleReset = async () => {
  try {
    await ElMessageBox.confirm(
      t('settings.messages.confirmResetNotificationSettings'),
      t('settings.messages.warning'),
      {
        confirmButtonText: t('settings.confirm'),
        cancelButtonText: t('settings.cancel'),
        type: 'warning'
      }
    )
    settings.value = {
      enabled: false,
      email_enabled: false,
      email: '',
      smtp_host: '',
      smtp_port: 587,
      smtp_username: '',
      smtp_password: '',
      webhook_enabled: false,
      webhook_url: '',
      webhook_secret: '',
      dingtalk_enabled: false,
      dingtalk_webhook: '',
      dingtalk_secret: '',
      sms_enabled: false,
      sms_provider: '',
      sms_api_key: '',
      sms_template_id: '',
      sms_sign_name: '',
      // 通知事件
      event_scan_success: true,
      event_scan_error: true
    }
    ElMessage.success(t('settings.messages.notificationSettingsReset'))
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('settings.messages.resetNotificationSettingsFailed'))
    }
  }
}

const handleNotifySubmit = () => {
  notifyForm.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      await axios.put('/settings', settings.value)
      ElMessage.success(t('settings.messages.notificationSettingsSaved'))
    } catch (error) {
      ElMessage.error(t('settings.messages.saveNotificationSettingsFailed'))
    } finally {
      saving.value = false
    }
  })
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.settings-container {
  padding: 20px;
  background: var(--bg-color);
  min-height: 100vh;
  color: var(--text-color);
}

.header {
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: var(--text-color);
}

.settings-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: var(--text-color);
}

.card-header .el-icon {
  color: #667eea;
  margin-right: 8px;
}

.form-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 5px;
}

/* 通知设置样式 */
.notification-settings {
  max-width: 1000px;
}

.settings-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.settings-info h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
}

.settings-info p {
  margin: 4px 0 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.switch-content {
  padding: 20px;
  text-align: center;
}

.switch-content .el-switch {
  margin-bottom: 12px;
}

.switch-desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.notification-type-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 20px;
}

.notification-type-card.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.type-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--bg-color);
}

.type-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.type-icon {
  color: #409eff;
  font-size: 18px;
}

.type-title {
  font-weight: 600;
  color: var(--text-color);
  font-size: 16px;
}

.type-description {
  padding: 0 20px 20px 20px;
}

.type-description p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.notification-actions {
  text-align: center;
  padding: 20px 0;
}

.notification-actions .el-button {
  margin: 0 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-container {
    padding: 16px;
  }

  .settings-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .action-section {
    flex-direction: column;
  }

  .action-section .el-button {
    width: 100%;
  }
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.notification-card {
  animation: fadeInUp 0.5s ease-out;
}

.notification-card:nth-child(1) {
  animation-delay: 0.1s;
}

.notification-card:nth-child(2) {
  animation-delay: 0.2s;
}

.notification-card:nth-child(3) {
  animation-delay: 0.3s;
}

.notification-card:nth-child(4) {
  animation-delay: 0.4s;
}

.notification-card:nth-child(5) {
  animation-delay: 0.5s;
}

.notify-form {
  max-width: 1100px;
  margin: 0 auto;
}

.notify-card {
  border-radius: 16px;
  box-shadow: 0 2px 16px 0 rgba(64, 158, 255, 0.06);
  margin-bottom: 18px;
  transition: box-shadow 0.2s, opacity 0.2s;
  min-height: 260px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  position: relative;
}

.notify-card.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 16px;
  color: var(--text-color);
}

.notify-actions {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin: 32px 0 0 0;
}

.notify-section {
  background: var(--card-bg);
  border-radius: 16px;
  box-shadow: 0 2px 16px 0 rgba(64, 158, 255, 0.06);
  padding: 32px 32px 24px 32px;
  margin-bottom: 32px;
}

.notify-group-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  margin: 32px 0 12px 0;
  gap: 10px;
}

.notify-bar {
  width: 4px;
  height: 22px;
  border-radius: 2px;
  display: inline-block;
  margin-right: 8px;
}

.notify-bar.email {
  background: #409EFF;
}

.notify-bar.wechat {
  background: #07c160;
}

.notify-bar.event {
  background: #faad14;
}

.notify-bar.sms {
  background: #ff9800;
}

.notify-bar.dingtalk {
  background: #409EFF;
}

.notify-bar.webhook {
  background: #13c2c2;
}

.notify-title {
  margin-right: 16px;
}

.notify-switch {
  margin-left: auto;
}

.notify-switch-label {
  margin-left: 8px;
  color: #888;
  font-size: 14px;
}

.notify-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px 0 rgba(64, 158, 255, 0.06);
  margin-bottom: 18px;
  border: 1px solid #f0f0f0;
  background: #fff;
  transition: box-shadow 0.2s, opacity 0.2s;
}

.notify-card.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.notify-form-row {
  padding: 12px 0 0 0;
}

.event-card {
  background: #fafbfc;
  border: 1px solid #f0f0f0;
}

.event-row {
  padding: 12px 0 0 0;
}

.event-label {
  font-size: 15px;
  color: #333;
  margin-right: 12px;
}

.notify-actions-bar {
  display: flex;
  justify-content: flex-end;
  gap: 24px;
  margin: 32px 0 0 0;
  padding-bottom: 8px;
}

.notify-form-col {
  padding: 12px 0 0 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.flex-spacer {
  flex: 1;
}

.clickable {
  cursor: pointer;
  user-select: none;
}

.collapse-arrow {
  transition: transform 0.2s;
  margin-left: 8px;
}

.collapse-arrow.collapsed {
  transform: rotate(-90deg);
}

.notify-switch-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 8px 0 16px 0;
}

.switch-disabled {
  opacity: 0.5;
  pointer-events: none;
}
</style>