<template>
  <div class="alert-policies-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>{{ $t('alertPolicies.pageTitle') }}</h2>
        <p class="page-description">{{ $t('alertPolicies.pageDescription') }}</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon>
            <Plus />
          </el-icon>
          {{ $t('alertPolicies.createAlertPolicy') }}
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-form :model="filterForm" inline>
        <el-form-item :label="$t('alertPolicies.policyType')">
          <el-select v-model="filterForm.policy_type" :placeholder="$t('alertPolicies.allTypes')" clearable>
            <el-option :label="$t('alertPolicies.resourceAlert')" value="resource" />
            <el-option :label="$t('alertPolicies.eventAlert')" value="event" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('alertPolicies.alertLevel')">
          <el-select v-model="filterForm.level" :placeholder="$t('alertPolicies.allLevels')" clearable>
            <el-option :label="$t('alertPolicies.info')" value="info" />
            <el-option :label="$t('alertPolicies.warning')" value="warning" />
            <el-option :label="$t('alertPolicies.error')" value="error" />
            <el-option :label="$t('alertPolicies.critical')" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('alertPolicies.status')">
          <el-select v-model="filterForm.enabled" :placeholder="$t('alertPolicies.allStatus')" clearable>
            <el-option :label="$t('alertPolicies.enabled')" :value="true" />
            <el-option :label="$t('alertPolicies.disabled')" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="loadPolicies">{{ $t('alertPolicies.search') }}</el-button>
          <el-button @click="resetFilter">{{ $t('alertPolicies.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 策略列表 -->
    <div class="policies-container">
      <el-table :data="filteredPolicies" style="width: 100%" @selection-change="handleSelectionChange"
        v-loading="loading">
        <el-table-column type="selection" width="55" />

        <el-table-column prop="name" :label="$t('alertPolicies.alertName')" sortable>
          <template #default="{ row }">
            <el-link type="primary" @click="showPolicyDetail(row)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="resource_type" :label="$t('alertPolicies.resourceType')" sortable>
          <template #default="{ row }">
            {{ getResourceTypeLabel(row.resource_type) }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('alertPolicies.alertItems')" sortable>
          <template #default="{ row }">
            <div v-if="row.alert_items && row.alert_items.length > 0">
              <div v-for="item in row.alert_items.slice(0, 2)" :key="item">
                {{ getAlertItemLabel(item) }}{{ row.trigger_rules && row.trigger_rules[item] ?
                  `${row.trigger_rules[item].operator === 'gt' ? '>' : row.trigger_rules[item].operator === 'lt' ? '<'
                    : '='}${row.trigger_rules[item].threshold}%` : '' }} </div>
                  <div v-if="row.alert_items.length > 2" class="more-items">
                    +{{ row.alert_items.length - 2 }}{{ $t('alertPolicies.items') }}
                  </div>
              </div>
              <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="level" :label="$t('alertPolicies.alertLevel')" sortable>
          <template #default="{ row }">
            <el-tag :type="getLevelTagType(row.level)" size="small">
              {{ getLevelLabel(row.level) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="enabled" :label="$t('alertPolicies.enabledStatus')" sortable>
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? $t('alertPolicies.enabled') : $t('alertPolicies.disabled') }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="$t('alertPolicies.notificationTargets')" sortable>
          <template #default="{ row }">
            <div v-if="row.notification_targets && row.notification_targets.length > 0">
              <el-tag v-for="targetId in row.notification_targets.slice(0, 2)" :key="targetId" size="small" type="info"
                class="mr-1">
                {{ getNotificationTargetName(targetId) }}
              </el-tag>
              <el-tag v-if="row.notification_targets.length > 2" size="small" type="info">
                +{{ row.notification_targets.length - 2 }}
              </el-tag>
            </div>
            <span v-else class="text-muted">{{ $t('alertPolicies.none') }}</span>
          </template>
        </el-table-column>

        <el-table-column :label="$t('alertPolicies.monitoredResourcesCount')" sortable>
          <template #default="{ row }">
            {{ row.monitored_resources?.length || 0 }}
          </template>
        </el-table-column>

        <el-table-column prop="created_at" :label="$t('alertPolicies.createdTime')" sortable>
          <template #default="{ row }">
            <div class="time-display">
              <div>{{ formatDate(row.created_at).split(' ')[0] }}</div>
              <div class="time">{{ formatDate(row.created_at).split(' ')[1] }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('alertPolicies.actions')" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :type="row.enabled ? 'success' : 'info'" @click="togglePolicy(row)"
              :loading="row.toggling">
              {{ row.enabled ? $t('alertPolicies.disable') : $t('alertPolicies.enable') }}
            </el-button>
            <el-button size="small" @click="editPolicy(row)">{{ $t('alertPolicies.edit') }}</el-button>
            <el-button size="small" type="danger" @click="deletePolicy(row)">{{ $t('alertPolicies.delete')
              }}</el-button>
            <el-button size="small" type="warning" @click="testPolicy(row)">{{ $t('alertPolicies.test') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredPolicies.length === 0" class="empty-state">
        <el-empty :description="$t('alertPolicies.noAlertPolicies')" />
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog"
      :title="editingPolicy ? $t('alertPolicies.editAlertPolicy') : $t('alertPolicies.createAlertPolicy')" width="800px"
      @close="resetForm">
      <el-form ref="policyFormRef" :model="policyForm" :rules="policyRules" label-width="120px">
        <!-- 基本信息 -->
        <el-card class="form-section">
          <template #header>
            <span class="section-title">{{ $t('alertPolicies.basicInfo') }}</span>
          </template>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.policyName')" prop="name">
                <el-input v-model="policyForm.name" :placeholder="$t('alertPolicies.enterPolicyName')" maxlength="50"
                  show-word-limit />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.policyType')" prop="policy_type">
                <el-radio-group v-model="policyForm.policy_type" @change="handlePolicyTypeChange">
                  <el-radio label="resource">{{ $t('alertPolicies.resourceAlert') }}</el-radio>
                  <el-radio label="event">{{ $t('alertPolicies.eventAlert') }}</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.alertLevel')" prop="level">
                <el-select v-model="policyForm.level" :placeholder="$t('alertPolicies.selectAlertLevel')">
                  <el-option :label="$t('alertPolicies.info')" value="info" />
                  <el-option :label="$t('alertPolicies.warning')" value="warning" />
                  <el-option :label="$t('alertPolicies.error')" value="error" />
                  <el-option :label="$t('alertPolicies.critical')" value="critical" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.enabledStatus')">
                <el-switch v-model="policyForm.enabled" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item :label="$t('alertPolicies.policyDescription')" prop="description">
            <el-input v-model="policyForm.description" type="textarea" :rows="3"
              :placeholder="$t('alertPolicies.enterPolicyDescription')" maxlength="200" show-word-limit />
          </el-form-item>
        </el-card>

        <!-- 监控配置 -->
        <el-card class="form-section" v-if="isResourcePolicy">
          <template #header>
            <span class="section-title">{{ $t('alertPolicies.monitoringConfig') }}</span>
          </template>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.resourceType')" prop="resource_type">
                <el-select v-model="policyForm.resource_type" :placeholder="$t('alertPolicies.selectResourceType')"
                  @change="handleResourceTypeChange">
                  <el-option v-for="type in resourceTypes" :key="type.code" :label="type.name" :value="type.code" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.monitoredResources')" prop="monitored_resources">
                <el-button @click="openResourceSelector" type="primary" plain :disabled="!policyForm.resource_type">
                  {{ $t('alertPolicies.selectResources') }} ({{ policyForm.monitored_resources?.length || 0 }})
                </el-button>
                <div class="form-tip">{{ $t('alertPolicies.selectResourceTypeFirst') }}</div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item :label="$t('alertPolicies.alertItems')" prop="alert_items">
            <el-checkbox-group v-model="policyForm.alert_items">
              <el-checkbox v-for="item in resourceItems" :key="item.code" :label="item.code">
                {{ item.name }}
                <span v-if="item.unit" class="item-unit">({{ item.unit }})</span>
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <!-- 触发规则 -->
          <div v-if="policyForm.alert_items && policyForm.alert_items.length > 0">
            <el-divider content-position="left">{{ $t('alertPolicies.triggerRules') }}</el-divider>
            <div v-for="item in policyForm.alert_items" :key="item" class="trigger-rule">
              <div class="rule-header">
                <span class="rule-title">{{ getAlertItemLabel(item) }}</span>
                <el-button size="small" @click="removeTriggerRule(item)" type="danger" plain>
                  {{ $t('alertPolicies.deleteRule') }}
                </el-button>
              </div>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item :label="$t('alertPolicies.operator')" :prop="`trigger_rules.${item}.operator`">
                    <el-select v-model="policyForm.trigger_rules[item].operator">
                      <el-option :label="$t('alertPolicies.greaterThan')" value="gt" />
                      <el-option :label="$t('alertPolicies.lessThan')" value="lt" />
                      <el-option :label="$t('alertPolicies.equalTo')" value="eq" />
                      <el-option :label="$t('alertPolicies.notEqualTo')" value="ne" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="10">
                  <el-form-item :label="$t('alertPolicies.threshold')" :prop="`trigger_rules.${item}.threshold`">
                    <el-input-number v-model="policyForm.trigger_rules[item].threshold" :min="0" :max="100"
                      :precision="2" />
                  </el-form-item>
                </el-col>
                <el-col :span="10">
                  <el-form-item :label="$t('alertPolicies.durationSeconds')" :prop="`trigger_rules.${item}.duration`">
                    <el-input-number v-model="policyForm.trigger_rules[item].duration" :min="1" :max="3600" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>
          </div>
        </el-card>

        <!-- 事件配置 -->
        <el-card class="form-section" v-if="isEventPolicy">
          <template #header>
            <span class="section-title">{{ $t('alertPolicies.eventConfig') }}</span>
          </template>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.eventType')" prop="event_type">
                <el-select v-model="policyForm.event_type" :placeholder="$t('alertPolicies.selectEventType')"
                  @change="handleEventTypeChange">
                  <el-option v-for="type in eventTypes" :key="type.code" :label="type.name" :value="type.code" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.eventActions')" prop="event_actions">
                <el-select v-model="policyForm.event_actions" multiple
                  :placeholder="$t('alertPolicies.selectEventActions')">
                  <el-option v-for="action in eventActions" :key="action.code" :label="action.name"
                    :value="action.code" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item :label="$t('alertPolicies.eventResults')" prop="event_results">
            <el-checkbox-group v-model="policyForm.event_results">
              <el-checkbox v-for="result in eventResults" :key="result.code" :label="result.code">
                {{ result.name }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-card>

        <!-- 通知配置 -->
        <el-card class="form-section">
          <template #header>
            <span class="section-title">{{ $t('alertPolicies.notificationConfig') }}</span>
          </template>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.notificationChannels')" prop="notification_channels">
                <el-select v-model="policyForm.notification_channels" multiple
                  :placeholder="$t('alertPolicies.selectNotificationChannels')"
                  @change="handleNotificationChannelsChange">
                  <el-option v-for="channel in notificationChannels" :key="channel.id"
                    :label="`${channel.name} (${getChannelTypeName(channel.channel_type)})`" :value="channel.id" />
                </el-select>
                <div class="form-tip">{{ $t('alertPolicies.selectNotificationChannelsTip') }}</div>
                <!-- 兼容性信息提示 -->
                <div v-if="compatibilityInfo.message" class="compatibility-info">
                  <el-alert :title="compatibilityInfo.message" :type="compatibilityInfo.compatible ? 'info' : 'warning'"
                    :closable="false" show-icon />
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.alertTemplate')" prop="template_id">
                <el-select v-model="policyForm.template_id" :placeholder="$t('alertPolicies.selectAlertTemplate')"
                  clearable :disabled="!policyForm.notification_channels.length">
                  <el-option v-for="template in compatibleTemplates" :key="template.id"
                    :label="`${template.name} (${getTemplateTypeName(template.template_type)})`" :value="template.id" />
                </el-select>
                <div class="form-tip">{{ $t('alertPolicies.selectAlertTemplateTip') }}</div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.notificationTargets')" prop="notification_targets">
                <el-select v-model="policyForm.notification_targets" multiple
                  :placeholder="$t('alertPolicies.selectNotificationTargets')"
                  :disabled="!policyForm.notification_channels.length">
                  <el-option v-for="target in compatibleTargets" :key="target.id"
                    :label="`${target.name} (${getTargetTypeName(target.target_type)})`" :value="target.id" />
                </el-select>
                <div class="form-tip">{{ $t('alertPolicies.selectNotificationTargetsTip') }}</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="$t('alertPolicies.notificationCycle')" prop="notification_cycle">
                <el-select v-model="policyForm.notification_cycle"
                  :placeholder="$t('alertPolicies.selectNotificationCycle')">
                  <el-option :label="$t('alertPolicies.immediateNotification')" value="immediate" />
                  <el-option :label="$t('alertPolicies.fiveMinutes')" value="5min" />
                  <el-option :label="$t('alertPolicies.fifteenMinutes')" value="15min" />
                  <el-option :label="$t('alertPolicies.thirtyMinutes')" value="30min" />
                  <el-option :label="$t('alertPolicies.oneHour')" value="1hour" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item :label="$t('alertPolicies.retryCount')" prop="retry_count">
                <el-input-number v-model="policyForm.retry_count" :min="0" :max="10" controls-position="right" />
                <div class="form-tip">{{ $t('alertPolicies.retryCountTip') }}</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="$t('alertPolicies.rateLimitSeconds')" prop="rate_limit">
                <el-input-number v-model="policyForm.rate_limit" :min="60" :max="3600" controls-position="right" />
                <div class="form-tip">{{ $t('alertPolicies.rateLimitTip') }}</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="$t('alertPolicies.timeoutSeconds')" prop="timeout">
                <el-input-number v-model="policyForm.timeout" :min="10" :max="300" controls-position="right" />
                <div class="form-tip">{{ $t('alertPolicies.timeoutTip') }}</div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('alertPolicies.cancel') }}</el-button>
        <el-button type="primary" @click="savePolicy" :loading="saving">
          {{ editingPolicy ? $t('alertPolicies.update') : $t('alertPolicies.create') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 资源选择器 -->
    <el-dialog v-model="showResourceSelector"
      :title="$t('alertPolicies.selectMonitoringResources', { resourceType: getResourceTypeLabel(policyForm.resource_type) })"
      width="600px">
      <div class="selector-content">
        <div class="selector-header">
          <div class="resource-type-info">
            {{ $t('alertPolicies.currentResourceType') }}: <el-tag size="small">{{
              getResourceTypeLabel(policyForm.resource_type) }}</el-tag>
          </div>
          <div class="resource-count">
            {{ $t('alertPolicies.totalResources', { count: filteredResources.length }) }}
          </div>
        </div>
        <el-input v-model="resourceSearchKeyword" :placeholder="$t('alertPolicies.searchResources')" clearable>
          <template #prefix>
            <el-icon>
              <Search />
            </el-icon>
          </template>
        </el-input>
        <div class="resource-list">
          <el-checkbox-group v-model="selectedResources">
            <div v-for="resource in filteredResources" :key="resource.id" class="resource-item">
              <el-checkbox :label="resource.id">
                <div class="resource-info">
                  <span class="resource-name">{{ resource.name }}</span>
                  <span class="resource-type">{{ getResourceTypeLabel(policyForm.resource_type) }}</span>
                </div>
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </div>
      </div>

      <template #footer>
        <el-button @click="showResourceSelector = false">{{ $t('alertPolicies.cancel') }}</el-button>
        <el-button type="primary" @click="confirmResourceSelection">{{ $t('alertPolicies.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 策略详情侧拉抽屉 -->
    <el-drawer v-model="showPolicyDetailDrawer" :title="$t('alertPolicies.policyDetails')" direction="rtl" size="50%">
      <div v-if="selectedPolicy" class="policy-detail">
        <div class="detail-section">
          <h3>{{ $t('alertPolicies.basicInfo') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.policyName') }}:</span>
            <span class="value">{{ selectedPolicy.name }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.policyDescription') }}:</span>
            <span class="value">{{ selectedPolicy.description || $t('alertPolicies.noDescription') }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.policyType') }}:</span>
            <span class="value">{{ selectedPolicy.policy_type === 'resource' ? $t('alertPolicies.resourceMonitoring') :
              $t('alertPolicies.eventMonitoring') }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.alertLevel') }}:</span>
            <span class="value">
              <el-tag :type="getLevelTagType(selectedPolicy.level)" size="small">
                {{ getLevelLabel(selectedPolicy.level) }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.enabledStatus') }}:</span>
            <span class="value">
              <el-tag :type="selectedPolicy.enabled ? 'success' : 'info'" size="small">
                {{ selectedPolicy.enabled ? $t('alertPolicies.enabled') : $t('alertPolicies.disabled') }}
              </el-tag>
            </span>
          </div>
        </div>

        <div class="detail-section" v-if="selectedPolicy.policy_type === 'resource'">
          <h3>{{ $t('alertPolicies.monitoringConfig') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.resourceType') }}:</span>
            <span class="value">{{ getResourceTypeLabel(selectedPolicy.resource_type) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.monitoredResources') }}:</span>
            <span class="value">{{ selectedPolicy.monitored_resources?.length || 0 }}{{ $t('alertPolicies.items')
              }}</span>
          </div>
          <div class="detail-item"
            v-if="selectedPolicy.monitored_resources && selectedPolicy.monitored_resources.length > 0">
            <span class="label">{{ $t('alertPolicies.resourceList') }}:</span>
            <div class="value">
              <el-tag v-for="resource in selectedPolicy.monitored_resources" :key="resource.id" size="small"
                style="margin-right: 8px; margin-bottom: 4px;">
                {{ resource.name }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>{{ $t('alertPolicies.alertConfig') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.alertItems') }}:</span>
            <span class="value">{{ selectedPolicy.alert_items?.length || 0 }}{{ $t('alertPolicies.items') }}</span>
          </div>
          <div class="detail-item" v-if="selectedPolicy.alert_items && selectedPolicy.alert_items.length > 0">
            <span class="label">{{ $t('alertPolicies.alertRules') }}:</span>
            <div class="value">
              <div v-for="item in selectedPolicy.alert_items" :key="item" class="rule-item">
                <span class="rule-name">{{ getAlertItemLabel(item) }}</span>
                <span v-if="selectedPolicy.trigger_rules && selectedPolicy.trigger_rules[item]" class="rule-condition">
                  {{ selectedPolicy.trigger_rules[item].operator === 'gt' ? '>' :
                    selectedPolicy.trigger_rules[item].operator === 'lt' ? '<' :
                      selectedPolicy.trigger_rules[item].operator === 'eq' ? '=' : '!=' }} {{
                      selectedPolicy.trigger_rules[item].threshold }}% ({{ $t('alertPolicies.duration') }}{{
                      selectedPolicy.trigger_rules[item].duration }}{{ $t('alertPolicies.seconds') }}) </span>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>{{ $t('alertPolicies.notificationConfig') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.notificationTemplate') }}:</span>
            <span class="value">{{ selectedPolicy.template_name || $t('alertPolicies.notSet') }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.notificationTargets') }}:</span>
            <span class="value">{{ selectedPolicy.notification_targets?.length || 0 }}{{ $t('alertPolicies.items')
              }}</span>
          </div>
          <div class="detail-item"
            v-if="selectedPolicy.notification_targets && selectedPolicy.notification_targets.length > 0">
            <span class="label">{{ $t('alertPolicies.notificationList') }}:</span>
            <div class="value">
              <el-tag v-for="target in selectedPolicy.notification_targets" :key="target.id" size="small"
                style="margin-right: 8px; margin-bottom: 4px;">
                {{ target.name }}
              </el-tag>
            </div>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.notificationCycle') }}:</span>
            <span class="value">{{ selectedPolicy.notification_cycle || $t('alertPolicies.immediate') }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h3>{{ $t('alertPolicies.otherInfo') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.createdTime') }}:</span>
            <span class="value">{{ formatDate(selectedPolicy.created_at) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.updatedTime') }}:</span>
            <span class="value">{{ formatDate(selectedPolicy.updated_at) }}</span>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" @click="editPolicy(selectedPolicy)">{{ $t('alertPolicies.editPolicy') }}</el-button>
          <el-button @click="testPolicy(selectedPolicy)">{{ $t('alertPolicies.testPolicy') }}</el-button>
          <el-button :type="selectedPolicy.enabled ? 'warning' : 'success'" @click="togglePolicy(selectedPolicy)"
            :loading="selectedPolicy.toggling">
            {{ selectedPolicy.enabled ? $t('alertPolicies.disable') : $t('alertPolicies.enable') }}
          </el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 通知对象选择器 -->
    <el-dialog v-model="showNotificationSelector" :title="$t('alertPolicies.selectNotificationTargets')" width="600px" :close-on-click-modal="false">
      <div class="selector-content">
        <el-input v-model="notificationSearchKeyword" :placeholder="$t('alertPolicies.searchNotificationTargets')"
          clearable>
          <template #prefix>
            <el-icon>
              <Search />
            </el-icon>
          </template>
        </el-input>
        <div class="notification-list">
          <el-checkbox-group v-model="selectedNotifications">
            <div v-for="target in filteredNotifications" :key="target.id" class="notification-item">
              <el-checkbox :label="target.id">
                <div class="notification-info">
                  <span class="notification-name">{{ target.name }}</span>
                  <span class="notification-type">{{ target.type }}</span>
                </div>
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </div>
      </div>

      <template #footer>
        <el-button @click="showNotificationSelector = false">{{ $t('alertPolicies.cancel') }}</el-button>
        <el-button type="primary" @click="confirmNotificationSelection">{{ $t('alertPolicies.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import axios from '@/utils/axios.mjs'

const { t } = useI18n()

// 响应式数据
const loading = ref(false)
const policies = ref([])
const availableResources = ref([])
const notificationTargets = ref([])
const notificationChannels = ref([])
const templates = ref([])
const compatibleTemplates = ref([])
const compatibleTargets = ref([])
const compatibilityInfo = ref({})
const policyFormRef = ref()

// 告警定义数据
const resourceTypes = ref([])
const resourceItems = ref([])
const eventTypes = ref([])
const eventActions = ref([])
const eventResults = ref([])

// 筛选表单
const filterForm = reactive({
  policy_type: '',
  level: '',
  enabled: null
})

// 策略表单
const policyForm = reactive({
  name: '',
  description: '',
  policy_type: 'resource',
  level: 'warning',
  enabled: true,
  resource_type: '',
  monitored_resources: [],
  alert_items: [],
  trigger_rules: {},
  event_type: '',
  event_actions: [],
  event_results: [],
  template_id: '',
  notification_channels: [],
  notification_targets: [],
  notification_cycle: 'immediate',
  retry_count: 3,
  rate_limit: 300,
  timeout: 30
})

// 表单验证规则
const policyRules = {
  name: [
    { required: true, message: t('alertPolicies.validation.enterPolicyName'), trigger: 'blur' },
    { min: 2, max: 50, message: t('alertPolicies.validation.policyNameLength'), trigger: 'blur' }
  ],
  policy_type: [
    { required: true, message: t('alertPolicies.validation.selectPolicyType'), trigger: 'change' }
  ],
  level: [
    { required: true, message: t('alertPolicies.validation.selectAlertLevel'), trigger: 'change' }
  ],
  description: [
    { max: 200, message: t('alertPolicies.validation.descriptionLength'), trigger: 'blur' }
  ]
}

// 弹窗控制
const showCreateDialog = ref(false)
const showResourceSelector = ref(false)
const showNotificationSelector = ref(false)
const showPolicyDetailDrawer = ref(false)
const editingPolicy = ref(null)
const selectedPolicy = ref(null)
const saving = ref(false)

// 选择器数据
const resourceSearchKeyword = ref('')
const selectedResources = ref([])
const filteredResources = computed(() => {
  let filtered = availableResources.value

  // 只根据搜索关键词过滤
  if (resourceSearchKeyword.value) {
    const keyword = resourceSearchKeyword.value.toLowerCase()
    filtered = filtered.filter(resource =>
      resource.name.toLowerCase().includes(keyword) ||
      (resource.type && resource.type.toLowerCase().includes(keyword)) ||
      (resource.group && resource.group.toLowerCase().includes(keyword))
    )
  }

  return filtered
})

const notificationSearchKeyword = ref('')
const selectedNotifications = ref([])
const filteredNotifications = computed(() => {
  if (!notificationSearchKeyword.value) return notificationTargets.value
  const keyword = notificationSearchKeyword.value.toLowerCase()
  return notificationTargets.value.filter(target =>
    target.name.toLowerCase().includes(keyword) ||
    target.type.toLowerCase().includes(keyword)
  )
})

// 计算属性
const isResourcePolicy = computed(() => policyForm.policy_type === 'resource')
const isEventPolicy = computed(() => policyForm.policy_type === 'event')

const filteredPolicies = computed(() => {
  let result = policies.value

  if (filterForm.policy_type) {
    result = result.filter(policy => policy.policy_type === filterForm.policy_type)
  }

  if (filterForm.level) {
    result = result.filter(policy => policy.level === filterForm.level)
  }

  if (filterForm.enabled !== null) {
    result = result.filter(policy => policy.enabled === filterForm.enabled)
  }

  return result
})

// 方法
const loadPolicies = async () => {
  try {
    loading.value = true
    const response = await axios.get('/alerts/policies')
    policies.value = response.data.policies || []
  } catch (error) {
    ElMessage.error(t('alertPolicies.messages.loadPoliciesFailed'))
  } finally {
    loading.value = false
  }
}

const loadResources = async () => {
  try {
    let apiUrl = ''
    switch (policyForm.resource_type) {
      case 'client':
        apiUrl = '/api/clients'
        break
      case 'proxy_node':
        apiUrl = '/nodes'
        break
      case 'storage_node':
        apiUrl = '/storages'
        break
      default:
        apiUrl = '/nodes'
    }

    const response = await axios.get(apiUrl)
    availableResources.value = response.data.data || []
  } catch (error) {
    console.error(t('alertPolicies.logMessages.loadResourcesFailed'), error)
  }
}

const loadNotificationTargets = async () => {
  try {
    const response = await axios.get('/notifications/targets')
    notificationTargets.value = response.data.targets || []
  } catch (error) {
    console.error(t('alertPolicies.logMessages.loadNotificationTargetsFailed'), error)
  }
}

const loadNotificationChannels = async () => {
  try {
    const response = await axios.get('/notifications/channels')
    notificationChannels.value = response.data.channels || []
  } catch (error) {
    console.error(t('alertPolicies.logMessages.loadNotificationChannelsFailed'), error)
  }
}

const loadTemplates = async () => {
  try {
    const response = await axios.get('/alerts/templates')
    templates.value = response.data.templates || []
  } catch (error) {
    console.error(t('alertPolicies.logMessages.loadTemplatesFailed'), error)
  }
}

// 新增：加载告警定义数据
const loadAlertDefinitions = async () => {
  try {
    // 加载资源类型
    const resourceTypesResponse = await axios.get('/alerts/resource-types')
    resourceTypes.value = resourceTypesResponse.data.resource_types || []

    // 加载事件类型
    const eventTypesResponse = await axios.get('/alerts/event-types')
    eventTypes.value = eventTypesResponse.data.event_types || []

    // 加载事件结果
    const eventResultsResponse = await axios.get('/alerts/event-results')
    eventResults.value = eventResultsResponse.data.event_results || []

  } catch (error) {
    console.error(t('alertPolicies.logMessages.getAlertDefinitionsFailed'), error)
  }
}

// 新增：根据资源类型加载资源条目
const loadResourceItems = async (resourceTypeCode) => {
  try {
    const response = await axios.get(`/api/alerts/resource-items?resource_type_code=${resourceTypeCode}`)
    resourceItems.value = response.data.resource_items || []
  } catch (error) {
    console.error(t('alertPolicies.logMessages.getResourceItemsFailed'), error)
  }
}

// 新增：根据事件类型加载事件动作

// 获取通知对象名称
const getNotificationTargetName = (targetId) => {
  const target = notificationTargets.value.find(t => t.id === targetId)
  return target ? target.name : targetId
}

// 处理通知渠道变化
const handleNotificationChannelsChange = async () => {
  if (!policyForm.notification_channels.length) {
    compatibleTemplates.value = []
    compatibleTargets.value = []
    policyForm.template_id = ''
    policyForm.notification_targets = []
    return
  }

  try {
    // 获取选择的渠道类型
    const selectedChannels = notificationChannels.value.filter(
      channel => policyForm.notification_channels.includes(channel.id)
    )
    const channelTypes = selectedChannels.map(channel => channel.channel_type)

    // 获取兼容的模板
    const templatesQueryString = channelTypes.map(type => `channel_types=${encodeURIComponent(type)}`).join('&')
    const templatesResponse = await axios.get(`/api/notifications/compatible-templates?${templatesQueryString}`)
    compatibleTemplates.value = templatesResponse.data.templates || []

    // 获取兼容的通知对象
    const targetsQueryString = channelTypes.map(type => `channel_types=${encodeURIComponent(type)}`).join('&')
    const targetsResponse = await axios.get(`/api/notifications/compatible-targets?${targetsQueryString}`)
    compatibleTargets.value = targetsResponse.data.targets || []

    // 获取兼容性信息
    const compatibilityResponse = await axios.get(`/api/alerts/policies/compatibility-info?${templatesQueryString}`)
    compatibilityInfo.value = compatibilityResponse.data

    // 清除不兼容的选择
    if (policyForm.template_id) {
      const templateExists = compatibleTemplates.value.find(t => t.id === policyForm.template_id)
      if (!templateExists) {
        policyForm.template_id = ''
      }
    }

    if (policyForm.notification_targets.length) {
      policyForm.notification_targets = policyForm.notification_targets.filter(targetId => {
        return compatibleTargets.value.find(t => t.id === targetId)
      })
    }

  } catch (error) {
    console.error(t('alertPolicies.logMessages.getCompatibilityDataFailed'), error)
    ElMessage.error(t('alertPolicies.messages.getCompatibilityDataFailed'))
  }
}

// 获取渠道类型显示名称
const getChannelTypeName = (type) => {
  const typeNames = {
    'email': t('alertPolicies.channelTypes.email'),
    'sms': t('alertPolicies.channelTypes.sms'),
    'webhook': t('alertPolicies.channelTypes.webhook'),
    'dingtalk': t('alertPolicies.channelTypes.dingtalk'),
    'slack': t('alertPolicies.channelTypes.slack')
  }
  return typeNames[type] || type
}

// 获取模板类型显示名称
const getTemplateTypeName = (type) => {
  return getChannelTypeName(type)
}

// 获取对象类型显示名称
const getTargetTypeName = (type) => {
  return getChannelTypeName(type)
}
const loadEventActions = async (eventTypeCode) => {
  try {
    const response = await axios.get(`/api/alerts/event-actions?event_type_code=${eventTypeCode}`)
    eventActions.value = response.data.event_actions || []
  } catch (error) {
    console.error(t('alertPolicies.logMessages.getEventActionsFailed'), error)
  }
}

const resetFilter = () => {
  filterForm.policy_type = ''
  filterForm.level = ''
  filterForm.enabled = null
  loadPolicies()
}

const openCreateDialog = () => {
  editingPolicy.value = null
  resetPolicyForm()
  showCreateDialog.value = true
}

const editPolicy = async (policy) => {
  editingPolicy.value = policy
  Object.assign(policyForm, {
    name: policy.name,
    description: policy.description || '',
    policy_type: policy.policy_type,
    level: policy.level,
    enabled: policy.enabled,
    resource_type: policy.resource_type || '',
    monitored_resources: policy.monitored_resources || [],
    alert_items: policy.alert_items || [],
    trigger_rules: policy.trigger_rules || {},
    event_type: policy.event_type || '',
    event_actions: policy.event_actions || [],
    event_results: policy.event_results || [],
    template_id: policy.template_id || '',
    notification_channels: policy.notification_channels || [],
    notification_targets: policy.notification_targets || [],
    notification_cycle: policy.notification_cycle || 'immediate',
    retry_count: policy.retry_count || 3,
    rate_limit: policy.rate_limit || 300,
    timeout: policy.timeout || 30
  })

  // 确保trigger_rules中的每个alert_item都有完整的规则对象
  if (policyForm.alert_items && policyForm.alert_items.length > 0) {
    policyForm.alert_items.forEach(item => {
      if (!policyForm.trigger_rules[item] || !policyForm.trigger_rules[item].operator) {
        policyForm.trigger_rules[item] = {
          operator: policyForm.trigger_rules[item]?.operator || 'gt',
          threshold: policyForm.trigger_rules[item]?.threshold || 80,
          duration: policyForm.trigger_rules[item]?.duration || 60
        }
      }
    })
  }

  showCreateDialog.value = true

  // 如果有通知渠道，加载兼容数据
  if (policy.notification_channels && policy.notification_channels.length > 0) {
    await handleNotificationChannelsChange()
  }
}

const resetPolicyForm = () => {
  Object.assign(policyForm, {
    name: '',
    description: '',
    policy_type: 'resource',
    level: 'warning',
    enabled: true,
    resource_type: '',
    monitored_resources: [],
    alert_items: [],
    trigger_rules: {},
    event_type: '',
    event_actions: [],
    event_results: [],
    template_id: '',
    notification_channels: [],
    notification_targets: [],
    notification_cycle: 'immediate',
    retry_count: 3,
    rate_limit: 300,
    timeout: 30
  })
  policyFormRef.value?.resetFields()
}

const handlePolicyTypeChange = () => {
  if (policyForm.policy_type === 'resource') {
    policyForm.event_type = ''
    policyForm.event_actions = []
    policyForm.event_results = []
    policyForm.trigger_rules = {}
  } else {
    policyForm.resource_type = ''
    policyForm.monitored_resources = []
    policyForm.alert_items = []
    policyForm.trigger_rules = {}
  }
}

const handleResourceTypeChange = async () => {
  policyForm.monitored_resources = []
  policyForm.alert_items = []
  policyForm.trigger_rules = {}

  if (policyForm.resource_type) {
    await loadResourceItems(policyForm.resource_type)
  }
  loadResources()
}

const handleEventTypeChange = async () => {
  policyForm.event_actions = []

  if (policyForm.event_type) {
    await loadEventActions(policyForm.event_type)
  }
}

const openResourceSelector = () => {
  if (!policyForm.resource_type) {
    ElMessage.warning(t('alertPolicies.messages.selectResourceTypeFirst'))
    return
  }
  showResourceSelector.value = true
  selectedResources.value = policyForm.monitored_resources.map(r => r.id)
}

const confirmResourceSelection = () => {
  policyForm.monitored_resources = filteredResources.value.filter(r => selectedResources.value.includes(r.id))
  showResourceSelector.value = false
}

const openNotificationSelector = () => {
  showNotificationSelector.value = true
  selectedNotifications.value = policyForm.notification_targets.map(t => t.id)
}

const confirmNotificationSelection = () => {
  policyForm.notification_targets = notificationTargets.value.filter(target => selectedNotifications.value.includes(target.id))
  showNotificationSelector.value = false
}

const showPolicyDetail = (policy) => {
  selectedPolicy.value = policy
  showPolicyDetailDrawer.value = true
}

const removeTriggerRule = (item) => {
  delete policyForm.trigger_rules[item]
  policyForm.alert_items = policyForm.alert_items.filter(i => i !== item)
}

const togglePolicy = async (policy) => {
  try {
    policy.toggling = true
    const response = await axios.put(`/api/alerts/policies/${policy.id}`, {
      enabled: policy.enabled
    })
    ElMessage.success(policy.enabled ? t('alertPolicies.messages.policyEnabled') : t('alertPolicies.messages.policyDisabled'))
  } catch (error) {
    policy.enabled = !policy.enabled // 恢复状态
    ElMessage.error(t('alertPolicies.messages.operationFailed'))
  } finally {
    policy.toggling = false
  }
}

const testPolicy = async (policy) => {
  try {
    await axios.post(`/api/alerts/policies/${policy.id}/test`)
    ElMessage.success(t('alertPolicies.messages.testAlertSent'))
  } catch (error) {
    ElMessage.error(t('alertPolicies.messages.testFailed'))
  }
}

const deletePolicy = async (policy) => {
  try {
    await ElMessageBox.confirm(
      t('alertPolicies.messages.confirmDeletePolicy', { policyName: policy.name }),
      t('alertPolicies.messages.confirmDelete'),
      {
        confirmButtonText: t('alertPolicies.messages.confirm'),
        cancelButtonText: t('alertPolicies.messages.cancel'),
        type: 'warning'
      }
    )

    await axios.delete(`/api/alerts/policies/${policy.id}`)
    ElMessage.success(t('alertPolicies.messages.deleteSuccess'))
    loadPolicies()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('alertPolicies.messages.deleteFailed'))
    }
  }
}

const savePolicy = async () => {
  try {
    await policyFormRef.value.validate()
    saving.value = true

    const data = { ...policyForm }

    // 验证配置
    const validationResponse = await axios.post('/alerts/policies/validate-configuration', {
      notification_channels: data.notification_channels,
      template_id: data.template_id,
      notification_targets: data.notification_targets
    })

    const validationResult = validationResponse.data

    if (!validationResult.valid) {
      ElMessage.error(t('alertPolicies.messages.configValidationFailed') + ': ' + validationResult.errors.join('; '))
      return
    }

    if (validationResult.warnings.length > 0) {
      const confirmed = await ElMessageBox.confirm(
        t('alertPolicies.messages.configWarnings') + '\n' + validationResult.warnings.join('\n'),
        t('alertPolicies.messages.configWarning'),
        {
          confirmButtonText: t('alertPolicies.messages.continue'),
          cancelButtonText: t('alertPolicies.messages.cancel'),
          type: 'warning'
        }
      ).catch(() => false)

      if (!confirmed) {
        return
      }
    }

    if (editingPolicy.value) {
      await axios.put(`/api/alerts/policies/${editingPolicy.value.id}`, data)
      ElMessage.success(t('alertPolicies.messages.updateSuccess'))
    } else {
      await axios.post('/alerts/policies', data)
      ElMessage.success(t('alertPolicies.messages.createSuccess'))
    }

    showCreateDialog.value = false
    loadPolicies()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(editingPolicy.value ? t('alertPolicies.messages.updateFailed') : t('alertPolicies.messages.createFailed'))
    }
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  resetPolicyForm()
}

// 工具方法
const getLevelLabel = (level) => {
  const labels = {
    info: t('alertPolicies.info'),
    warning: t('alertPolicies.warning'),
    error: t('alertPolicies.error'),
    critical: t('alertPolicies.critical')
  }
  return labels[level] || level
}

const getLevelTagType = (level) => {
  const types = {
    info: 'info',
    warning: 'warning',
    error: 'danger',
    critical: 'danger'
  }
  return types[level] || 'info'
}

const getPolicyTypeLabel = (type) => {
  const labels = {
    resource: t('alertPolicies.resourceAlert'),
    event: t('alertPolicies.eventAlert')
  }
  return labels[type] || type
}

const getPolicyTypeTagType = (type) => {
  const types = {
    resource: 'primary',
    event: 'success'
  }
  return types[type] || 'info'
}

const getResourceTypeLabel = (code) => {
  const type = resourceTypes.value.find(t => t.code === code)
  return type ? type.name : code
}

const getAlertItemLabel = (code) => {
  const item = resourceItems.value.find(i => i.code === code)
  return item ? item.name : code
}

const getEventTypeLabel = (code) => {
  const type = eventTypes.value.find(t => t.code === code)
  return type ? type.name : code
}

const getEventActionLabel = (code) => {
  const action = eventActions.value.find(a => a.code === code)
  return action ? action.name : code
}

const getEventResultLabel = (code) => {
  const result = eventResults.value.find(r => r.code === code)
  return result ? result.name : code
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString()
}

// 监听告警条目变化，初始化触发规则
watch(() => policyForm.alert_items, (newItems, oldItems) => {
  // 初始化新选择的告警条目的触发规则
  newItems.forEach(item => {
    if (!policyForm.trigger_rules[item]) {
      policyForm.trigger_rules[item] = {
        operator: 'gt',
        threshold: 80,
        duration: 60
      }
    }
  })

  // 清理已移除的告警条目的触发规则
  if (oldItems) {
    oldItems.forEach(item => {
      if (!newItems.includes(item)) {
        delete policyForm.trigger_rules[item]
      }
    })
  }
}, { deep: true })

// 生命周期
onMounted(() => {
  loadPolicies()
  loadResources()
  loadNotificationTargets()
  loadNotificationChannels()
  loadTemplates()
  loadAlertDefinitions() // 新增：加载告警定义数据
})
</script>

<style scoped>
.mr-1 {
  margin-right: 4px;
}

.text-muted {
  color: #909399;
}

.compatibility-info {
  margin-top: 8px;
}

.compatibility-info .el-alert {
  margin-bottom: 0;
}

.alert-policies-page {
  padding: 20px;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left h2 {
  margin: 0 0 5px 0;
  color: var(--text-color);
  font-size: 24px;
}

.page-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.filter-bar {
  background: var(--card-bg);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.policies-container {
  margin-top: 20px;
}

.policy-card {
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
}

.policy-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.policy-card.disabled {
  opacity: 0.6;
}

/* 表格样式 */
.el-table {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table__header) {
  width: 100% !important;
}

:deep(.el-table__header th) {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
}

.time-display {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.time-display .time {
  font-size: 12px;
  color: (--text-color);
  margin-top: 2px;
}

.more-items {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.item-unit {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 4px;
}

/* 侧拉抽屉样式 */
.policy-detail {
  padding: 20px;
}

.detail-section {
  margin-bottom: 30px;
}

.detail-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
  color: (--text-color);
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.detail-item {
  display: flex;
  margin-bottom: 12px;
  align-items: flex-start;
}

.detail-item .label {
  width: 100px;
  font-weight: 500;
  color: (--text-color);
  flex-shrink: 0;
}

.detail-item .value {
  flex: 1;
  color: (--text-color);
}

.rule-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  padding: 8px;
  background: var(--card-bg);
  border-radius: 4px;
}

.rule-name {
  font-weight: 500;
  margin-right: 8px;
}

.rule-condition {
  color: var(--text-color);
  font-size: 14px;
}

.detail-actions {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 10px;
}

.card-header {
  padding: 20px 20px 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.policy-info {
  flex: 1;
}

.policy-name {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: (--text-color);
}

.policy-info .el-tag {
  margin-right: 8px;
}

.policy-status {
  margin-left: 16px;
}

.card-content {
  padding: 16px 20px;
}

.policy-description {
  margin: 0 0 16px 0;
  color: var(--text-color);
  font-size: 14px;
  line-height: 1.5;
}

.policy-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.detail-item .label {
  color: var(--text-color);
}

.detail-item .value {
  color: var(--text-color);
}

.card-actions {
  padding: 16px 20px 20px;
  display: flex;
  gap: 8px;
  border-top: 1px solid #f0f0f0;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.form-section {
  margin-bottom: 20px;
}

.section-title {
  font-weight: 600;
  color: var(--text-color);
}

.trigger-rule {
  background: var(--card-bg);
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.rule-title {
  font-weight: 600;
  color: var(--text-color);
}

.selector-content {
  max-height: 400px;
  overflow-y: auto;
}

.resource-list,
.notification-list {
  margin-top: 16px;
}

.resource-item,
.notification-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.resource-item:last-child,
.notification-item:last-child {
  border-bottom: none;
}

.resource-info,
.notification-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-left: 8px;
}

.resource-name,
.notification-name {
  font-weight: 500;
  color: var(--text-color);
}

.resource-type,
.notification-type {
  color: var(--text-color);
  font-size: 12px;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: var(--card-bg);
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--text-color);
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

:deep(.el-radio-group) {
  display: flex;
  gap: 16px;
}

.form-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  line-height: 1.4;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--card-bg);
  border-radius: 6px;
}

.resource-type-info {
  font-size: 14px;
  color: var(--text-color);
}

.resource-count {
  font-size: 12px;
  color: var(--text-color);
}
</style>