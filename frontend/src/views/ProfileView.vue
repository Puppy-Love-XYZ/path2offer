<template>
  <div class="profile-page">
    <el-alert v-if="isWelcome" title="🎉 注册成功！完善个人档案，让岗位匹配更精准" type="success" show-icon :closable="true"
      class="welcome-banner" @close="isWelcome = false" />

    <div class="page-greeting">
      <span class="greeting-wave">👋</span>
      <div class="greeting-content">
        <span class="greeting-hi">你好，<em>{{ form.real_name || profile.username }}</em> 同学！</span>
        <span class="greeting-tip">管理你的个人档案，让求职之路更顺畅。</span>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="profile-tabs" @tab-change="onMainTabChange">
      <el-tab-pane label="基本信息" name="basic">
        <el-form :model="form" :rules="basicFormRules" ref="basicFormRef" label-width="100px" class="profile-form">
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="姓名" prop="real_name">
                <el-input v-model="form.real_name" placeholder="请输入真实姓名" clearable />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="目标城市" prop="target_city">
                <el-select v-model="form.target_city" placeholder="请选择目标城市（可多选）" style="width:100%" multiple filterable
                  clearable collapse-tags :collapse-tags-tooltip="true">
                  <el-option v-for="city in availableCities" :key="city" :label="city" :value="city" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="期望薪资(K)">
                <div style="display:flex;gap:8px;align-items:center">
                  <el-input-number v-model="form.expected_salary_min" :min="1" :max="200" placeholder="下限"
                    style="flex:1" />
                  <span style="color:#909399">~</span>
                  <el-input-number v-model="form.expected_salary_max" :min="1" :max="200" placeholder="上限"
                    style="flex:1" />
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="工作年限" prop="work_experience">
                <el-select v-model="form.work_experience" placeholder="请选择" style="width:100%">
                  <el-option label="应届生" value="应届生" />
                  <el-option label="1年以内" value="1年以内" />
                  <el-option label="1-3年" value="1-3年" />
                  <el-option label="3-5年" value="3-5年" />
                  <el-option label="5-10年" value="5-10年" />
                  <el-option label="10年以上" value="10年以上" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="账号安全" name="security">
        <el-form class="profile-form security-form" label-width="100px">
          <el-form-item label="原密码">
            <el-input v-model="pwdForm.oldPassword" type="password" placeholder="请输入原密码" show-password clearable />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="pwdForm.newPassword" type="password" placeholder="请输入新密码" show-password clearable />
          </el-form-item>

          <el-form-item v-if="pwdForm.newPassword" label=" ">
            <div class="pwd-rules-grid">
              <div v-for="rule in pwdRules" :key="rule.key" :class="['pwd-rule-item', rule.passed ? 'pass' : 'fail']">
                <el-icon>
                  <Check v-if="rule.passed" />
                  <Close v-else />
                </el-icon>
                <span>{{ rule.label }}</span>
              </div>
            </div>
          </el-form-item>

          <el-form-item label="确认新密码">
            <el-input v-model="pwdForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password
              clearable />
            <div v-if="pwdForm.confirmPassword && pwdForm.newPassword !== pwdForm.confirmPassword" class="pwd-mismatch">
              两次密码不一致
            </div>
          </el-form-item>

          <el-form-item label=" ">
            <el-button type="primary" :loading="pwdSaving" :disabled="!pwdCanSubmit" @click="handleChangePassword">
              确认修改
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="收藏岗位" name="favorites">
        <div class="profile-form" style="padding-top:16px">
          <div v-if="favoritesState.loading" class="history-loading">
            <el-icon class="is-loading">
              <Loading />
            </el-icon> 加载中...
          </div>
          <el-empty v-else-if="!favoritesState.items.length" description="暂无收藏岗位" />
          <div v-else>
            <div class="fav-job-grid">
              <div v-for="item in favoritesState.items" :key="item.fav_id" class="fav-job-card"
                @click="openFavJobDetail(item.job_id)">
                <div class="fav-job-card-top">
                  <div class="fav-job-info">
                    <div class="fav-job-name">{{ item.job_name || '未知岗位' }}</div>
                    <div class="fav-job-company">{{ item.company_name || '' }}</div>
                  </div>
                  <el-button size="small" type="danger" text
                    @click.stop="unfavoriteJob(item.job_id, item.fav_id)">取消收藏</el-button>
                </div>
                <div class="fav-job-meta">
                  <el-tag v-if="item.work_city" size="small" type="info" effect="plain">{{ item.work_city }}</el-tag>
                  <el-tag v-if="item.job_salary" size="small" type="success" effect="plain">{{ item.job_salary
                  }}</el-tag>
                  <el-tag v-if="item.your_education" size="small" effect="plain">{{ item.your_education }}</el-tag>
                  <el-tag v-if="item.working_exp" size="small" effect="plain">{{ item.working_exp }}</el-tag>
                  <el-tag v-if="item.work_type" size="small" :type="item.work_type === '实习' ? 'warning' : 'primary'"
                    effect="plain">{{ item.work_type }}</el-tag>
                  <el-tag v-if="item.company_size" size="small" type="info" effect="plain">{{ item.company_size
                  }}</el-tag>
                </div>
                <div class="fav-job-date">收藏于 {{ item.favorited_at }}</div>
              </div>
            </div>
            <div class="history-pagination">
              <el-pagination v-model:current-page="favoritesState.page" :page-size="20" :total="favoritesState.total"
                layout="prev, pager, next" @current-change="loadFavorites" />
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="历史记录" name="history">
        <el-tabs v-model="historyTab" class="history-inner-tabs" @tab-change="onHistoryTabChange">

          <el-tab-pane label="简历分析" name="resume">
            <div v-if="resumeHistory.loading" class="history-loading">
              <el-icon class="is-loading">
                <Loading />
              </el-icon> 加载中...
            </div>
            <el-empty v-else-if="!resumeHistory.items.length" description="暂无简历分析记录" />
            <div v-else>
              <div v-for="item in resumeHistory.items" :key="item.id" class="history-card clickable"
                @click="openResumeDetail(item.id)">
                <div class="history-card-main">
                  <div class="history-card-left">
                    <span class="history-filename">{{ item.filename || '未命名文件' }}</span>
                    <div class="history-meta">
                      <span>{{ item.created_at }}</span>
                      <span v-if="item.char_count">· {{ item.char_count }} 字</span>
                      <span v-if="item.elapsed_seconds">· 耗时 {{ item.elapsed_seconds?.toFixed(1) }}s</span>
                    </div>
                  </div>
                  <div class="history-card-right">
                    <div v-if="item.overall_score != null" class="history-score-block">
                      <span class="history-score" :class="scoreClass(item.overall_score)">{{ item.overall_score
                      }}</span>
                      <span class="history-rating">{{ item.overall_rating }}</span>
                    </div>
                    <el-button size="small" type="primary" text>查看详情</el-button>
                    <el-button size="small" type="danger" text
                      @click.stop="deleteHistory('resume', item.id)">删除</el-button>
                  </div>
                </div>
              </div>
              <div class="history-pagination">
                <el-pagination v-model:current-page="resumeHistory.page" :page-size="10" :total="resumeHistory.total"
                  layout="prev, pager, next" @current-change="loadResumeHistory" />
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="岗位匹配" name="matching">
            <div v-if="matchingHistory.loading" class="history-loading">
              <el-icon class="is-loading">
                <Loading />
              </el-icon> 加载中...
            </div>
            <el-empty v-else-if="!matchingHistory.items.length" description="暂无岗位匹配记录" />
            <div v-else>
              <div v-for="item in matchingHistory.items" :key="item.id" class="history-card clickable"
                @click="openMatchingDetail(item)">
                <div class="history-card-main">
                  <div class="history-card-left">
                    <div class="history-filename">
                      <el-tag size="small" :type="item.mode === 'auto' ? 'primary' : 'success'" class="mode-tag">
                        {{ item.mode === 'auto' ? '智能推荐' : '指定匹配' }}
                      </el-tag>
                      <span>{{ item.job_name || (item.mode === 'auto' ? `推荐 Top${item.top_k}` : '未知岗位') }}</span>
                      <span v-if="item.company_name" class="company-name">{{ item.company_name }}</span>
                    </div>
                    <div class="history-meta">
                      <span>{{ item.created_at }}</span>
                      <span v-if="item.filename">· {{ item.filename }}</span>
                    </div>
                  </div>
                  <div class="history-card-right">
                    <div v-if="item.match_score != null" class="history-score-block">
                      <span class="history-score" :class="scoreClass(item.match_score)">
                        {{ item.match_score?.toFixed(1) }}%
                      </span>
                    </div>
                    <el-button size="small" type="primary" text>查看报告</el-button>
                    <el-button size="small" type="danger" text
                      @click.stop="deleteHistory('matching', item.id)">删除</el-button>
                  </div>
                </div>
                <div v-if="item.mode === 'auto' && item.result_json" class="history-auto-preview">
                  <span v-for="(m, i) in parseAutoResult(item.result_json)" :key="i" class="auto-match-chip">{{
                    m.job_name }} <b>{{ m.match_score?.toFixed(0) }}%</b></span>
                </div>
              </div>
              <div class="history-pagination">
                <el-pagination v-model:current-page="matchingHistory.page" :page-size="10"
                  :total="matchingHistory.total" layout="prev, pager, next" @current-change="loadMatchingHistory" />
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="模拟面试" name="interview">
            <div v-if="interviewHistory.loading" class="history-loading">
              <el-icon class="is-loading">
                <Loading />
              </el-icon> 加载中...
            </div>
            <el-empty v-else-if="!interviewHistory.items.length" description="暂无模拟面试记录" />
            <div v-else>
              <div v-for="item in interviewHistory.items" :key="item.id" class="history-card clickable"
                @click="openInterviewDetail(item.id)">
                <div class="history-card-main">
                  <div class="history-card-left">
                    <div class="history-filename">
                      <el-tag size="small" type="warning" class="mode-tag">{{ item.style_name || item.style }}</el-tag>
                      <span>{{ item.job_name || '通用面试' }}</span>
                    </div>
                    <div class="history-meta">
                      <span>{{ item.created_at }}</span>
                      <span>· {{ item.turns }} 轮问答</span>
                      <span v-if="item.duration_seconds">· {{ formatDuration(item.duration_seconds) }}</span>
                    </div>
                  </div>
                  <div class="history-card-right">
                    <el-button size="small" type="primary" text>查看详情</el-button>
                    <el-button size="small" type="danger" text
                      @click.stop="deleteHistory('interview', item.id)">删除</el-button>
                  </div>
                </div>
              </div>
              <div class="history-pagination">
                <el-pagination v-model:current-page="interviewHistory.page" :page-size="10"
                  :total="interviewHistory.total" layout="prev, pager, next" @current-change="loadInterviewHistory" />
              </div>
            </div>
          </el-tab-pane>

        </el-tabs>
      </el-tab-pane>
    </el-tabs>

    <div v-if="activeTab === 'basic'" class="save-bar">
      <el-button type="primary" size="large" :loading="saving" @click="handleSave">
        保存档案
      </el-button>
    </div>

    <el-dialog v-model="resumeDialogVisible" title="简历分析详情" width="860px" top="5vh"
      :before-close="() => resumeDialogVisible = false">
      <div v-if="resumeDetailLoading" class="dialog-loading">
        <el-icon class="is-loading">
          <Loading />
        </el-icon> 加载中...
      </div>
      <div v-else-if="resumeDetailData" class="rd-body">

        <div class="rd-meta">
          <span class="rd-filename">📄 {{ resumeDetailData.filename || '未命名文件' }}</span>
          <span class="rd-meta-item" v-if="resumeDetailData.created_at">{{ resumeDetailData.created_at }}</span>
          <span class="rd-meta-item" v-if="resumeDetailData.char_count">{{ resumeDetailData.char_count }} 字</span>
          <span class="rd-meta-item" v-if="resumeDetailData.elapsed_seconds">耗时 {{
            resumeDetailData.elapsed_seconds?.toFixed(1) }}s</span>
        </div>

        <div class="rd-overview">
          <div :class="['rd-rating-badge', rdRatingCls(resumeParsed?.evaluation?.overall_score)]">
            {{ resumeParsed?.evaluation?.overall_rating }}
          </div>
          <div class="rd-score-num">{{ resumeParsed?.evaluation?.overall_score }}<small> / 100</small></div>
          <p class="rd-summary">{{ resumeParsed?.evaluation?.summary }}</p>
        </div>

        <div v-if="resumeDimEntries.length" class="rd-section">
          <div class="rd-section-title">📊 维度综合评估</div>
          <div class="rd-dims-grid">
            <div v-for="([key, dim]) in resumeDimEntries" :key="key" class="rd-dim-card">
              <div class="rd-dim-head">
                <span class="rd-dim-icon">{{ dim.icon }}</span>
                <span class="rd-dim-label">{{ dim.label }}</span>
                <span class="rd-dim-score" :style="{ color: rdScoreClr(dim.score) }">{{ dim.score }}</span>
              </div>
              <div class="rd-dim-bar">
                <div class="rd-dim-fill" :style="{ width: dim.score + '%', background: rdScoreClr(dim.score) }"></div>
              </div>
              <div class="rd-dim-row">
                <span class="rd-dim-rating" :style="{ color: rdScoreClr(dim.score) }">{{ dim.rating }}</span>
                <span class="rd-dim-weight">权重 {{ dim.weight }}%</span>
              </div>
              <p v-if="dim.detail" class="rd-dim-detail">{{ dim.detail }}</p>
            </div>
          </div>
        </div>

        <div v-if="resumeDimEntries.length" class="rd-section">
          <div class="rd-section-title">🔍 各维度详细分析</div>
          <el-collapse accordion>
            <el-collapse-item v-for="([key, dim]) in resumeDimEntries" :key="key" :name="key">
              <template #title>
                <div class="rd-acc-title">
                  <span>{{ dim.icon }} {{ dim.label }}</span>
                  <span :style="{ color: rdScoreClr(dim.score), fontWeight: 700, fontSize: '13px' }">{{ dim.score }} 分 ·
                    {{ dim.rating }}</span>
                </div>
              </template>
              <div class="rd-acc-body">
                <p v-if="dim.detail" class="rd-acc-p">{{ dim.detail }}</p>
                <div v-if="dim.highlights?.length">
                  <div class="rd-tag rd-tag-green">✅ 亮点优势</div>
                  <ul>
                    <li v-for="(h, i) in dim.highlights" :key="i">{{ h }}</li>
                  </ul>
                </div>
                <div v-if="dim.issues?.length">
                  <div class="rd-tag rd-tag-red">⚠️ 问题短板</div>
                  <ul>
                    <li v-for="(iss, i) in dim.issues" :key="i">{{ iss }}</li>
                  </ul>
                </div>
                <div v-if="dim.suggestions?.length">
                  <div class="rd-tag rd-tag-blue">💡 改进建议</div>
                  <ul>
                    <li v-for="(sg, i) in dim.suggestions" :key="i">{{ sg }}</li>
                  </ul>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <div v-if="resumeParsed?.evaluation?.strengths?.length || resumeParsed?.evaluation?.weaknesses?.length"
          class="rd-section">
          <div class="rd-sw-grid">
            <div v-if="resumeParsed?.evaluation?.strengths?.length" class="rd-sw-col rd-strengths">
              <div class="rd-sw-title">💪 核心优势</div>
              <ul>
                <li v-for="(s, i) in resumeParsed.evaluation.strengths" :key="i">{{ s }}</li>
              </ul>
            </div>
            <div v-if="resumeParsed?.evaluation?.weaknesses?.length" class="rd-sw-col rd-weaknesses">
              <div class="rd-sw-title">🔧 待改进项</div>
              <ul>
                <li v-for="(w, i) in resumeParsed.evaluation.weaknesses" :key="i">{{ w }}</li>
              </ul>
            </div>
          </div>
        </div>

        <div v-if="resumeParsed?.evaluation?.key_recommendations?.length" class="rd-section">
          <div class="rd-section-title">🎯 优先优化建议</div>
          <div v-for="(rec, i) in resumeParsed.evaluation.key_recommendations" :key="i"
            :class="['rd-rec', rec.priority === '高' ? 'rd-rec-high' : rec.priority === '中' ? 'rd-rec-mid' : 'rd-rec-low']">
            <div class="rd-rec-hd">
              <span>{{ rec.priority === '高' ? '🔴 高优先级' : rec.priority === '中' ? '🟡 中优先级' : '🟢 低优先级' }}</span>
              <span class="rd-rec-cat">{{ rec.category }}</span>
            </div>
            <p><strong>{{ rec.action }}</strong></p>
            <p v-if="rec.example" class="rd-rec-eg">💡 {{ rec.example }}</p>
          </div>
        </div>

        <div v-if="resumeParsed?.jd_match" class="rd-section">
          <div class="rd-section-title">🎯 JD 精确匹配</div>
          <div class="rd-jdm-overview">
            <div
              :class="['rd-jdm-badge', resumeParsed.jd_match.overall_match === 'High' ? 'jdm-high' : resumeParsed.jd_match.overall_match === 'Medium' ? 'jdm-mid' : 'jdm-low']">
              {{ resumeParsed.jd_match.overall_match === 'High' ? '高度匹配' : resumeParsed.jd_match.overall_match ===
                'Medium' ?
                '中度匹配' : '匹配较低' }}
            </div>
            <span class="rd-jdm-pct">{{ resumeParsed.jd_match.match_percentage }}%</span>
            <p>{{ resumeParsed.jd_match.summary }}</p>
          </div>
          <div v-if="resumeParsed.jd_match.final_verdict" class="rd-verdict">
            🏆 {{ resumeParsed.jd_match.final_verdict }}
          </div>
        </div>

        <el-empty v-if="!resumeParsed" description="该记录暂无详细报告数据（早期记录未保存完整内容）" />
      </div>
    </el-dialog>

    <el-dialog v-model="matchingDialogVisible"
      :title="matchingDialogItem?.mode === 'auto' ? '智能推荐匹配报告' : `指定匹配报告 · ${matchingDialogItem?.job_name || ''}`"
      width="680px" top="5vh" :before-close="() => matchingDialogVisible = false">
      <div v-if="matchingDialogItem" class="md-body">

        <div class="md-meta">
          <el-tag size="small" :type="matchingDialogItem.mode === 'auto' ? 'primary' : 'success'">
            {{ matchingDialogItem.mode === 'auto' ? '智能推荐' : '指定匹配' }}
          </el-tag>
          <span v-if="matchingDialogItem.filename" class="md-meta-text">📄 {{ matchingDialogItem.filename }}</span>
          <span class="md-meta-text">{{ matchingDialogItem.created_at }}</span>
        </div>

        <template v-if="matchingDialogItem.mode === 'specific'">
          <div class="md-score-row">
            <div class="md-score-big" :class="scoreClass(matchingDialogItem.match_score ?? 0)">
              {{ matchingDialogItem.match_score?.toFixed(2) }}
            </div>
            <div class="md-score-info">
              <div class="md-job-name">{{ matchingDialogItem.job_name }}</div>
              <div class="md-company">{{ matchingDialogItem.company_name }}</div>
            </div>
          </div>
          <template v-if="matchingParsedResult?.report?.dimensions">
            <div class="md-dims">
              <div v-for="(dim, key) in matchingParsedResult.report.dimensions" :key="key" class="md-dim-row">
                <span class="md-dim-label">{{ dim.label }}</span>
                <div class="md-dim-bar-wrap">
                  <div class="md-dim-bar-fill" :style="{ width: dim.score + '%', background: rdScoreClr(dim.score) }">
                  </div>
                </div>
                <span class="md-dim-score" :style="{ color: rdScoreClr(dim.score) }">{{ Math.round(dim.score) }}</span>
                <span v-if="dim.match" class="md-dim-match">{{ dim.match }}</span>
                <span v-else-if="dim.matched_skills?.length" class="md-dim-match">{{ dim.matched_skills.slice(0,
                  5).join(' · ') }}</span>
              </div>
            </div>
          </template>
          <template v-if="matchingParsedDeep">
            <div v-if="matchingParsedDeep.strengths?.length" class="md-block md-block--green">
              <div class="md-block-title">✅ 优势亮点</div>
              <ul>
                <li v-for="(s, i) in matchingParsedDeep.strengths" :key="i">{{ s }}</li>
              </ul>
            </div>
            <div v-if="matchingParsedDeep.weaknesses?.length" class="md-block md-block--orange">
              <div class="md-block-title">⚠️ 差距不足</div>
              <ul>
                <li v-for="(w, i) in matchingParsedDeep.weaknesses" :key="i">{{ w }}</li>
              </ul>
            </div>
            <div v-if="matchingParsedDeep.advice?.length" class="md-block md-block--blue">
              <div class="md-block-title">💡 投递建议</div>
              <ul>
                <li v-for="(a, i) in matchingParsedDeep.advice" :key="i">{{ a }}</li>
              </ul>
            </div>
          </template>
        </template>

        <template v-else>
          <div class="md-auto-list">
            <div v-for="(m, i) in parseAutoResult(matchingDialogItem.result_json || '[]')" :key="i"
              class="md-auto-item">
              <span class="md-auto-rank" :class="'rank-' + (Number(i) + 1)">#{{ Number(i) + 1 }}</span>
              <div class="md-auto-info">
                <div class="md-auto-job">{{ m.job_name }}</div>
                <div class="md-auto-company">{{ m.company_name }}</div>
                <div class="md-auto-tags">
                  <span v-if="m.work_city" class="md-tag">{{ m.work_city }}</span>
                  <span class="md-tag g md-tag--salary">
                    {{ m.job_salary || `¥${m.salary_min}–${m.salary_max}k` }}
                  </span>
                  <span v-if="m.your_education" class="md-tag">{{ m.your_education }}</span>
                  <span v-if="m.working_exp" class="md-tag">{{ m.working_exp }}</span>
                </div>
                <div v-if="m.report?.dimensions" class="md-auto-dims">
                  <span v-if="m.report.dimensions.semantic" class="md-dim-pill md-dim-sem">
                    语义理解 {{ Math.round(m.report.dimensions.semantic.score) }}
                  </span>
                  <span v-if="m.report.dimensions.skills" class="md-dim-pill md-dim-skill">
                    技能匹配 {{ Math.round(m.report.dimensions.skills.score) }}
                  </span>
                  <span v-if="m.report.dimensions.experience" class="md-dim-pill md-dim-exp">
                    经验修正 {{ Math.round(m.report.dimensions.experience.score) }}
                  </span>
                </div>
              </div>
              <div class="md-auto-score" :class="scoreClass(m.match_score ?? 0)">
                {{ (m.match_score ?? 0).toFixed(2) }}
              </div>
            </div>
          </div>
        </template>

        <el-empty v-if="matchingDialogItem.mode === 'specific' && !matchingParsedResult && !matchingParsedDeep"
          description="该记录暂无详细报告数据" />
      </div>
    </el-dialog>

    <el-dialog v-model="interviewDialogVisible" title="面试详情" width="760px" class="interview-dialog"
      :before-close="() => interviewDialogVisible = false">
      <div v-if="interviewDetailLoading" class="dialog-loading">
        <el-icon class="is-loading">
          <Loading />
        </el-icon> 加载中...
      </div>
      <div v-else-if="interviewDetail">
        <div class="interview-detail-meta">
          <el-tag type="warning">{{ interviewDetail.style_name || interviewDetail.style }}</el-tag>
          <span v-if="interviewDetail.job_name">{{ interviewDetail.job_name }}</span>
          <span>{{ interviewDetail.turns }} 轮 · {{ formatDuration(interviewDetail.duration_seconds ?? 0) }}</span>
          <span class="interview-date">{{ interviewDetail.created_at }}</span>
        </div>

        <div class="interview-history-list">
          <div v-for="(msg, i) in interviewDetail.history" :key="i"
            :class="['interview-msg', msg.role === 'user' ? 'msg-user' : 'msg-ai']">
            <div class="msg-role">{{ msg.role === 'user' ? '我' : '面试官' }}</div>
            <div class="msg-content">{{ msg.content }}</div>
          </div>
        </div>

        <div v-if="interviewDetail.summary" class="interview-summary">
          <div class="summary-title">面试总结</div>
          <div class="summary-content">{{ interviewDetail.summary }}</div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="favJobDialogVisible" title="岗位详情" width="600px"
      :before-close="() => favJobDialogVisible = false">
      <div v-if="favJobDetailLoading" class="dialog-loading">
        <el-icon class="is-loading">
          <Loading />
        </el-icon> 加载中...
      </div>
      <div v-else-if="favJobDetail" class="fav-job-dialog-content">
        <h3 class="fav-dialog-title">{{ favJobDetail.job_name }}</h3>
        <p class="fav-dialog-company">{{ favJobDetail.company_name }}</p>
        <div class="fav-dialog-tags">
          <el-tag v-if="favJobDetail.work_city">{{ favJobDetail.work_city }}</el-tag>
          <el-tag v-if="favJobDetail.job_salary" type="success">{{ favJobDetail.job_salary }}</el-tag>
          <el-tag v-if="favJobDetail.your_education" type="info">{{ favJobDetail.your_education }}</el-tag>
          <el-tag v-if="favJobDetail.working_exp">{{ favJobDetail.working_exp }}</el-tag>
          <el-tag v-if="favJobDetail.company_size" type="warning">{{ favJobDetail.company_size }}</el-tag>
          <el-tag v-if="favJobDetail.work_type" :type="favJobDetail.work_type === '实习' ? 'warning' : 'primary'">{{
            favJobDetail.work_type }}</el-tag>
        </div>
        <div v-if="favJobDetail.job_summary" class="fav-dialog-section">
          <div class="fav-dialog-label">岗位描述</div>
          <p class="fav-dialog-text">{{ favJobDetail.job_summary }}</p>
        </div>
        <div v-if="favJobDetail.company_benefits" class="fav-dialog-section">
          <div class="fav-dialog-label">福利待遇</div>
          <p class="fav-dialog-text">{{ favJobDetail.company_benefits }}</p>
        </div>
        <div v-if="favJobDetail.work_major" class="fav-dialog-section">
          <div class="fav-dialog-label">专业要求</div>
          <p class="fav-dialog-text">{{ favJobDetail.work_major }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, toRaw } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Check, Close } from '@element-plus/icons-vue'
import { apiGetProfile, apiUpdateProfile, apiChangePassword, type UserProfile } from '../api/auth'
import { useAuth } from '@/composables/useAuth'
import {
  apiGetResumeHistory, apiGetMatchingHistory, apiGetInterviewHistory,
  apiGetInterviewDetail, apiGetResumeDetail, apiDeleteHistory,
  type ResumeHistoryItem, type MatchingHistoryItem, type InterviewHistoryItem,
  type InterviewRecordDetail, type ResumeHistoryDetail,
} from '@/api/history'
import {
  fetchFavorites, removeFavorite, fetchJobDetail, fetchFilterOptions,
  type FavoriteJobItem,
} from '@/api/matching'

const { setDisplayName } = useAuth()

const route = useRoute()
const isWelcome = ref(route.query.welcome === '1')
const activeTab = ref((route.query.tab as string) || 'basic')
const saving = ref(false)

const availableCities = ref<string[]>([])

const profile = reactive<Partial<UserProfile> & { completion: number; username: string }>({
  completion: 0,
  username: '',
})

const form = reactive({
  real_name: '',
  phone: '',
  gender: '',
  birth_year: undefined as number | undefined,
  location: '',
  school: '',
  major: '',
  degree: '',
  graduation_year: undefined as number | undefined,
  target_position: '',
  target_city: [] as string[],
  expected_salary_min: undefined as number | undefined,
  expected_salary_max: undefined as number | undefined,
  work_experience: '',
  tech_skills: '[]',
  about_me: '',
})

const basicFormRef = ref()
const basicFormRules = {
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  target_city: [{ required: true, message: '请选择目标城市', trigger: 'change' }],
  work_experience: [{ required: true, message: '请选择工作年限', trigger: 'change' }],
}

onMounted(async () => {
  try {
    const opts = await fetchFilterOptions()
    availableCities.value = opts.cities
  } catch { }

  try {
    const data = await apiGetProfile()
    Object.assign(profile, data)
    for (const key of Object.keys(form) as (keyof typeof form)[]) {
      const val = (data as any)[key]
      if (val !== null && val !== undefined) {
        if (key === 'target_city') {
          (form as any)[key] = typeof val === 'string' ? val.split(',').filter(Boolean) : (val || [])
        } else {
          (form as any)[key] = val
        }
      }
    }
    if (data.real_name) setDisplayName(data.real_name)
  } catch (e: any) {
    ElMessage.error('加载档案失败：' + (e.message || ''))
  }
})

async function handleSave() {
  try {
    await basicFormRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const payload: Record<string, any> = {}
    for (const [k, v] of Object.entries(toRaw(form))) {
      if (k === 'target_city') {
        payload[k] = Array.isArray(v) && (v as string[]).length > 0 ? (v as string[]).join(',') : null
      } else {
        payload[k] = (v === '' || v === undefined) ? null : v
      }
    }
    const data = await apiUpdateProfile(payload)
    Object.assign(profile, data)
    if (form.real_name) setDisplayName(form.real_name)
    ElMessage.success('档案已保存')
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e.message || ''))
  } finally {
    saving.value = false
  }
}

const historyTab = ref('resume')

function onMainTabChange(tab: string) {
  if (tab === 'history') {
    onHistoryTabChange(historyTab.value)
  }
  if (tab === 'favorites' && !favoritesState.loaded) {
    loadFavorites(1)
  }
}

function onHistoryTabChange(tab: string) {
  if (tab === 'resume' && !resumeHistory.loaded) loadResumeHistory(1)
  if (tab === 'matching' && !matchingHistory.loaded) loadMatchingHistory(1)
  if (tab === 'interview' && !interviewHistory.loaded) loadInterviewHistory(1)
}

const resumeHistory = reactive({
  items: [] as ResumeHistoryItem[],
  total: 0,
  page: 1,
  loading: false,
  loaded: false,
})

async function loadResumeHistory(page = 1) {
  resumeHistory.loading = true
  resumeHistory.page = page
  try {
    const res = await apiGetResumeHistory(page)
    resumeHistory.items = res.items
    resumeHistory.total = res.total
    resumeHistory.loaded = true
  } catch {
    ElMessage.error('加载简历分析历史失败')
  } finally {
    resumeHistory.loading = false
  }
}

const matchingHistory = reactive({
  items: [] as MatchingHistoryItem[],
  total: 0,
  page: 1,
  loading: false,
  loaded: false,
})

async function loadMatchingHistory(page = 1) {
  matchingHistory.loading = true
  matchingHistory.page = page
  try {
    const res = await apiGetMatchingHistory(page)
    matchingHistory.items = res.items
    matchingHistory.total = res.total
    matchingHistory.loaded = true
  } catch {
    ElMessage.error('加载岗位匹配历史失败')
  } finally {
    matchingHistory.loading = false
  }
}

const interviewHistory = reactive({
  items: [] as InterviewHistoryItem[],
  total: 0,
  page: 1,
  loading: false,
  loaded: false,
})

async function loadInterviewHistory(page = 1) {
  interviewHistory.loading = true
  interviewHistory.page = page
  try {
    const res = await apiGetInterviewHistory(page)
    interviewHistory.items = res.items
    interviewHistory.total = res.total
    interviewHistory.loaded = true
  } catch {
    ElMessage.error('加载面试记录失败')
  } finally {
    interviewHistory.loading = false
  }
}

async function deleteHistory(type: 'resume' | 'matching' | 'interview', id: number) {
  try {
    await ElMessageBox.confirm('确定删除此记录？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await apiDeleteHistory(type, id)
    ElMessage.success('已删除')
    if (type === 'resume') loadResumeHistory(resumeHistory.page)
    if (type === 'matching') loadMatchingHistory(matchingHistory.page)
    if (type === 'interview') loadInterviewHistory(interviewHistory.page)
  } catch {
    ElMessage.error('删除失败')
  }
}

interface RdDimension {
  score: number
  rating: string
  weight: number
  icon: string
  label: string
  detail?: string
  highlights?: string[]
  issues?: string[]
  suggestions?: string[]
}

const resumeDialogVisible = ref(false)
const resumeDetailLoading = ref(false)
const resumeDetailData = ref<ResumeHistoryDetail | null>(null)
const resumeParsed = computed(() => {
  if (!resumeDetailData.value?.result_json) return null
  try { return JSON.parse(resumeDetailData.value.result_json) } catch { return null }
})
const resumeDimEntries = computed<[string, RdDimension][]>(() =>
  Object.entries(resumeParsed.value?.evaluation?.dimensions || {}) as [string, RdDimension][]
)
const rdScoreClr = (s: number) => s >= 80 ? '#10B981' : s >= 65 ? '#3B82F6' : s >= 50 ? '#F59E0B' : '#EF4444'
const rdRatingCls = (s?: number) => {
  if (!s) return ''
  if (s >= 80) return 'rd-badge-excellent'
  if (s >= 65) return 'rd-badge-good'
  if (s >= 50) return 'rd-badge-avg'
  return 'rd-badge-poor'
}

async function openResumeDetail(id: number) {
  resumeDialogVisible.value = true
  resumeDetailLoading.value = true
  resumeDetailData.value = null
  try {
    resumeDetailData.value = await apiGetResumeDetail(id)
  } catch {
    ElMessage.error('加载简历分析详情失败')
    resumeDialogVisible.value = false
  } finally {
    resumeDetailLoading.value = false
  }
}

const interviewDialogVisible = ref(false)
const interviewDetailLoading = ref(false)
const interviewDetail = ref<InterviewRecordDetail | null>(null)

async function openInterviewDetail(id: number) {
  interviewDialogVisible.value = true
  interviewDetailLoading.value = true
  interviewDetail.value = null
  try {
    interviewDetail.value = await apiGetInterviewDetail(id)
  } catch {
    ElMessage.error('加载面试详情失败')
    interviewDialogVisible.value = false
  } finally {
    interviewDetailLoading.value = false
  }
}

const favoritesState = reactive({
  items: [] as FavoriteJobItem[],
  total: 0,
  page: 1,
  loading: false,
  loaded: false,
})

async function loadFavorites(page = 1) {
  favoritesState.loading = true
  favoritesState.page = page
  try {
    const res = await fetchFavorites(page, 20)
    favoritesState.items = res.items
    favoritesState.total = res.total
    favoritesState.loaded = true
  } catch {
    ElMessage.error('加载收藏岗位失败')
  } finally {
    favoritesState.loading = false
  }
}

async function unfavoriteJob(jobId: number, _favId: number) {
  try {
    await ElMessageBox.confirm('确定取消收藏此岗位？', '提示', { type: 'warning' })
  } catch { return }
  try {
    await removeFavorite(jobId)
    ElMessage.success('已取消收藏')
    loadFavorites(favoritesState.page)
  } catch {
    ElMessage.error('操作失败')
  }
}

const favJobDialogVisible = ref(false)
const favJobDetailLoading = ref(false)
const favJobDetail = ref<any>(null)

async function openFavJobDetail(jobId: number) {
  favJobDialogVisible.value = true
  favJobDetailLoading.value = true
  favJobDetail.value = null
  try {
    favJobDetail.value = await fetchJobDetail(jobId)
  } catch {
    ElMessage.error('获取岗位详情失败')
    favJobDialogVisible.value = false
  } finally {
    favJobDetailLoading.value = false
  }
}

function scoreClass(score: number) {
  if (score >= 80) return 'score-excellent'
  if (score >= 65) return 'score-good'
  if (score >= 50) return 'score-avg'
  return 'score-poor'
}

function formatDuration(sec: number) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return m > 0 ? `${m}分${s}秒` : `${s}秒`
}

function parseAutoResult(json: string) {
  try { return JSON.parse(json) } catch { return [] }
}

const matchingDialogVisible = ref(false)
const matchingDialogItem = ref<MatchingHistoryItem | null>(null)

const matchingParsedResult = computed(() => {
  if (!matchingDialogItem.value?.result_json) return null
  try { return JSON.parse(matchingDialogItem.value.result_json) } catch { return null }
})

const matchingParsedDeep = computed(() => matchingParsedResult.value?.deep_analysis ?? null)

function openMatchingDetail(item: MatchingHistoryItem) {
  matchingDialogItem.value = item
  matchingDialogVisible.value = true
}

const pwdSaving = ref(false)
const pwdForm = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })

function _hasSequentialChars(pwd: string, len = 6): boolean {
  for (let i = 0; i <= pwd.length - len; i++) {
    const win = pwd.slice(i, i + len)
    const diffs = Array.from({ length: len - 1 }, (_, j) => win.charCodeAt(j + 1) - win.charCodeAt(j))
    if (diffs.every(d => d === 1) || diffs.every(d => d === -1)) return true
  }
  return false
}

const pwdRules = computed(() => {
  const p = pwdForm.newPassword
  return [
    { key: 'length', label: '长度 8-20 位', passed: p.length >= 8 && p.length <= 20 },
    { key: 'letter', label: '包含字母', passed: /[a-zA-Z]/.test(p) },
    { key: 'digit', label: '包含数字', passed: /[0-9]/.test(p) },
    { key: 'special', label: '包含特殊符号', passed: /[!@#$%^&*()\-_=+\[\]{};:'",.<>/?\\|`~]/.test(p) },
    { key: 'noRepeat', label: '无 4+ 连续相同字符', passed: !/(.)\1{3,}/.test(p) },
    { key: 'noSeq', label: '无 6+ 连续顺序字符', passed: !_hasSequentialChars(p) },
  ]
})

const pwdCanSubmit = computed(() =>
  pwdForm.oldPassword.length > 0 &&
  pwdRules.value.every(r => r.passed) &&
  pwdForm.newPassword === pwdForm.confirmPassword &&
  pwdForm.confirmPassword.length > 0
)

async function handleChangePassword() {
  if (!pwdCanSubmit.value) return
  pwdSaving.value = true
  try {
    await apiChangePassword(pwdForm.oldPassword, pwdForm.newPassword)
    ElMessage.success('密码修改成功，请重新登录')
    pwdForm.oldPassword = ''
    pwdForm.newPassword = ''
    pwdForm.confirmPassword = ''
  } catch (e: any) {
    ElMessage.error(e.message || '修改失败')
  } finally {
    pwdSaving.value = false
  }
}
</script>

<style scoped>
.profile-page {
  padding: 24px;
  max-width: 960px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.welcome-banner {
  margin-bottom: 20px;
  border-radius: 8px;
}

.page-greeting {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #EEF4F2 0%, #F5FAF8 100%);
  border-radius: 12px;
  border: 1px solid rgba(26, 60, 52, 0.12);
  box-shadow: 0 2px 8px rgba(26, 60, 52, 0.06);
}

.greeting-wave {
  font-size: 20px;
  display: inline-block;
  animation: greet-wave 2.5s ease-in-out infinite;
  transform-origin: 70% 70%;
}

@keyframes greet-wave {

  0%,
  60%,
  100% {
    transform: rotate(0deg);
  }

  10%,
  30% {
    transform: rotate(20deg);
  }

  20% {
    transform: rotate(-8deg);
  }
}

.greeting-content {
  flex: 1;
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}

.greeting-hi {
  font-size: 15px;
  font-weight: 600;
  color: #1A3C34;
}

.greeting-hi em {
  font-style: normal;
  color: #1A3C34;
  font-weight: 700;
}

.greeting-tip {
  font-size: 13px;
  color: #4A7C68;
}

.profile-tabs {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 20px;
  width: 100%;
  box-sizing: border-box;
}

.profile-tabs :deep(.el-tabs__content),
.profile-tabs :deep(.el-tab-pane) {
  width: 100%;
}

.profile-form {
  padding-top: 16px;
}

.skill-input-area {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-height: 36px;
  padding: 4px 0;
}

.skill-tag {
  font-size: 13px;
}

.skill-input {
  width: 120px;
}

.save-bar {
  display: flex;
  justify-content: flex-end;
  padding: 0 4px;
}

.history-inner-tabs {
  margin-top: 8px;
}

.history-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 40px 0;
  justify-content: center;
  color: #909399;
  font-size: 14px;
}

.history-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 10px;
  background: #fafafa;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.history-card.clickable {
  cursor: pointer;
}

.history-card.clickable:hover {
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.12);
}

.history-card-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.history-card-left {
  flex: 1;
  min-width: 0;
}

.history-filename {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.company-name {
  font-size: 13px;
  color: #606266;
  font-weight: 400;
}

.history-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.history-card-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.history-score-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 48px;
}

.history-score {
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
}

.history-rating {
  font-size: 11px;
  color: #606266;
  margin-top: 2px;
}

.score-excellent {
  color: #4A7C59;
}

.score-good {
  color: #6366f1;
}

.score-avg {
  color: #e6a23c;
}

.score-poor {
  color: #f56c6c;
}

.mode-tag {
  flex-shrink: 0;
}

.history-auto-preview {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.auto-match-chip {
  font-size: 12px;
  background: #f5f3ff;
  color: #4338ca;
  padding: 2px 8px;
  border-radius: 10px;
}

.history-pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.security-form {
  max-width: 480px;
  padding-top: 16px;
}

.pwd-rules-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  padding: 10px 12px;
  background: #f8f9fb;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  width: 100%;
}

.pwd-rule-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  transition: color 0.2s;
}

.pwd-rule-item.pass {
  color: #4A7C59;
}

.pwd-rule-item.fail {
  color: #c0c4cc;
}

.pwd-mismatch {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}

.dialog-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  padding: 40px 0;
  color: #909399;
}

.interview-detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #606266;
  flex-wrap: wrap;
}

.interview-date {
  margin-left: auto;
}

.interview-history-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.interview-msg {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.interview-msg.msg-user {
  flex-direction: row-reverse;
}

.msg-role {
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  white-space: nowrap;
  padding-top: 4px;
  min-width: 32px;
  text-align: center;
}

.msg-content {
  max-width: 78%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.msg-user .msg-content {
  background: #f5f3ff;
  color: #303133;
}

.msg-ai .msg-content {
  background: #f4f4f5;
  color: #303133;
}

.interview-summary {
  margin-top: 16px;
  background: #f0f9eb;
  border-radius: 8px;
  padding: 14px 16px;
}

.summary-title {
  font-size: 13px;
  font-weight: 600;
  color: #4A7C59;
  margin-bottom: 8px;
}

.summary-content {
  font-size: 13px;
  color: #303133;
  line-height: 1.7;
  white-space: pre-wrap;
}

.fav-job-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.fav-job-card {
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  padding: 14px;
  cursor: pointer;
  background: #fafafa;
  transition: all 0.2s;
}

.fav-job-card:hover {
  border-color: #6366f1;
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.12);
}

.fav-job-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.fav-job-info {
  flex: 1;
  min-width: 0;
}

.fav-job-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fav-job-company {
  font-size: 12px;
  color: #606266;
  margin-top: 2px;
}

.fav-job-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 6px;
}

.fav-job-date {
  font-size: 11px;
  color: #c0c4cc;
}

.fav-job-dialog-content {
  padding: 4px 0;
}

.fav-dialog-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 4px;
  color: #303133;
}

.fav-dialog-company {
  font-size: 13px;
  color: #606266;
  margin: 0 0 12px;
}

.fav-dialog-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.fav-dialog-section {
  margin-bottom: 14px;
}

.fav-dialog-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
  padding-bottom: 5px;
  border-bottom: 1px solid #f1f5f9;
}

.fav-dialog-text {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
  margin: 0;
}

.rd-body {
  max-height: 78vh;
  overflow-y: auto;
  padding-right: 4px;
}

.rd-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 18px;
  border: 1px solid #e4e7ed;
}

.rd-filename {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rd-meta-item {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.rd-overview {
  text-align: center;
  padding: 20px 16px;
  background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%);
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid #e0d7ff;
}

.rd-rating-badge {
  display: inline-block;
  padding: 5px 20px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 8px;
}

.rd-badge-excellent {
  background: #d1fae5;
  color: #065f46;
}

.rd-badge-good {
  background: #dbeafe;
  color: #1e40af;
}

.rd-badge-avg {
  background: #fef3c7;
  color: #92400e;
}

.rd-badge-poor {
  background: #fee2e2;
  color: #991b1b;
}

.rd-score-num {
  font-size: 44px;
  font-weight: 900;
  color: #1e293b;
  line-height: 1.1;
  margin: 0 0 8px;
}

.rd-score-num small {
  font-size: 18px;
  color: #64748b;
  font-weight: 400;
}

.rd-summary {
  font-size: 13px;
  color: #64748b;
  line-height: 1.7;
  max-width: 620px;
  margin: 0 auto;
}

.rd-section {
  margin-bottom: 20px;
}

.rd-section-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #eef2ff;
}

.rd-dims-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.rd-dim-card {
  background: #f8fafc;
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  padding: 12px 14px;
}

.rd-dim-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.rd-dim-icon {
  font-size: 16px;
}

.rd-dim-label {
  flex: 1;
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
}

.rd-dim-score {
  font-size: 18px;
  font-weight: 800;
}

.rd-dim-bar {
  height: 5px;
  background: #e4e7ed;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 6px;
}

.rd-dim-fill {
  height: 100%;
  border-radius: 999px;
}

.rd-dim-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rd-dim-rating {
  font-size: 11px;
  color: #64748b;
}

.rd-dim-weight {
  font-size: 10px;
  color: #64748b;
  background: #eef2ff;
  padding: 1px 7px;
  border-radius: 999px;
}

.rd-dim-detail {
  margin: 6px 0 0;
  font-size: 11.5px;
  color: #64748b;
  line-height: 1.55;
}

.rd-acc-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  padding-right: 12px;
}

.rd-acc-body {
  padding: 4px 0 6px;
}

.rd-acc-p {
  font-size: 13px;
  color: #64748b;
  line-height: 1.7;
  margin: 0 0 10px;
}

.rd-acc-body ul {
  margin: 4px 0 10px;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rd-acc-body li {
  font-size: 12.5px;
  color: #64748b;
  line-height: 1.6;
}

.rd-tag {
  display: inline-block;
  font-size: 11.5px;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 6px;
  margin-bottom: 4px;
}

.rd-tag-green {
  background: #dcfce7;
  color: #14532d;
}

.rd-tag-red {
  background: #fee2e2;
  color: #7f1d1d;
}

.rd-tag-blue {
  background: #dbeafe;
  color: #1e3a8a;
}

.rd-sw-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.rd-sw-col {
  border-radius: 10px;
  padding: 14px 16px;
  border: 1px solid #e4e7ed;
}

.rd-strengths {
  border-top: 3px solid #10b981;
}

.rd-weaknesses {
  border-top: 3px solid #f59e0b;
}

.rd-sw-title {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 10px;
}

.rd-sw-col ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rd-sw-col li {
  font-size: 12.5px;
  color: #64748b;
  line-height: 1.6;
  padding-left: 14px;
  position: relative;
}

.rd-sw-col li::before {
  content: '•';
  position: absolute;
  left: 0;
  font-weight: 700;
}

.rd-strengths li::before {
  color: #10b981;
}

.rd-weaknesses li::before {
  color: #f59e0b;
}

.rd-rec {
  border-radius: 10px;
  padding: 12px 14px;
  border-left: 4px solid;
  background: #f8fafc;
  margin-bottom: 10px;
}

.rd-rec-high {
  border-color: #ef4444;
}

.rd-rec-mid {
  border-color: #f59e0b;
}

.rd-rec-low {
  border-color: #10b981;
}

.rd-rec-hd {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  font-size: 12.5px;
  font-weight: 700;
}

.rd-rec-cat {
  font-size: 11px;
  color: #64748b;
  background: #eef2ff;
  padding: 2px 8px;
  border-radius: 999px;
}

.rd-rec p {
  margin: 0 0 4px;
  font-size: 13px;
  color: #1e293b;
}

.rd-rec-eg {
  font-size: 12px;
  color: #64748b;
  background: rgba(0, 0, 0, 0.03);
  padding: 5px 9px;
  border-radius: 6px;
}

.rd-jdm-overview {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 10px;
  margin-bottom: 12px;
  border: 1px solid #e4e7ed;
}

.rd-jdm-badge {
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 700;
}

.jdm-high {
  background: #f0fdf4;
  color: #16a34a;
  border: 1.5px solid #bbf7d0;
}

.jdm-mid {
  background: #fffbeb;
  color: #d97706;
  border: 1.5px solid #fde68a;
}

.jdm-low {
  background: #fff1f2;
  color: #e11d48;
  border: 1.5px solid #fecdd3;
}

.rd-jdm-pct {
  font-size: 28px;
  font-weight: 800;
  color: #1e293b;
}

.rd-jdm-overview p {
  font-size: 13px;
  color: #64748b;
  margin: 0;
  flex: 1;
  min-width: 180px;
  line-height: 1.6;
}

.rd-verdict {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  background: linear-gradient(135deg, #faf5ff, #f0f9ff);
  border: 1.5px solid #e0d7ff;
  border-radius: 10px;
  padding: 12px 16px;
  line-height: 1.7;
}

.md-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.md-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding-bottom: 12px;
  border-bottom: 0.5px solid #EFEFEF;
}

.md-meta-text {
  font-size: 12.5px;
  color: #9CA3AF;
}

.md-score-row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 0;
  border-bottom: 0.5px solid #EFEFEF;
}

.md-score-big {
  font-family: 'Georgia', serif;
  font-size: 42px;
  font-weight: 400;
  line-height: 1;
  flex-shrink: 0;
}

.md-score-big.score-high {
  color: #1A3C34;
}

.md-score-big.score-good {
  color: #2C5749;
}

.md-score-big.score-ok {
  color: #D97706;
}

.md-score-big.score-low {
  color: #DC2626;
}

.md-job-name {
  font-size: 16px;
  font-weight: 600;
  color: #1A1A1A;
  margin-bottom: 4px;
}

.md-company {
  font-size: 12.5px;
  color: #9CA3AF;
}

.md-dims {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.md-dim-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.md-dim-label {
  width: 68px;
  font-size: 12px;
  color: #6B7280;
  text-align: right;
  flex-shrink: 0;
}

.md-dim-bar-wrap {
  flex: 1;
  height: 6px;
  background: #F0F0F0;
  border-radius: 999px;
  overflow: hidden;
}

.md-dim-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.md-dim-score {
  width: 28px;
  font-size: 12px;
  font-weight: 600;
  text-align: right;
  flex-shrink: 0;
}

.md-dim-match {
  font-size: 11.5px;
  color: #9CA3AF;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.md-block {
  border-radius: 4px;
  padding: 10px 14px;
  border: 0.5px solid;
}

.md-block--green {
  background: #EDF4EF;
  border-color: #9AC6B8;
}

.md-block--orange {
  background: #FAF3EB;
  border-color: #D4B87A;
}

.md-block--blue {
  background: #EEF4F2;
  border-color: #9AC6B8;
}

.md-block-title {
  font-size: 13px;
  font-weight: 600;
  color: #3D4451;
  margin-bottom: 8px;
}

.md-block ul {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.md-block li {
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
}

.md-auto-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.md-auto-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 8px;
  border-bottom: 0.5px solid #E2EDE9;
}

.md-auto-item:last-child {
  border-bottom: none;
}

.md-auto-rank {
  font-family: 'Georgia', serif;
  font-size: 14px;
  font-style: italic;
  font-weight: 700;
  width: 28px;
  flex-shrink: 0;
  padding-top: 2px;
}

.rank-1 {
  color: #B8860B;
}

.rank-2 {
  color: #6B7280;
}

.rank-3 {
  color: #8B4513;
}

.rank-4,
.rank-5 {
  color: #B8BAC0;
}

.md-auto-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.md-auto-job {
  font-size: 14px;
  font-weight: 600;
  color: #1A1A1A;
}

.md-auto-company {
  font-size: 12px;
  color: #9CA3AF;
}

.md-auto-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}

.md-tag {
  display: inline-block;
  padding: 1px 7px;
  font-size: 11px;
  border: 0.5px solid #C8D8D2;
  border-radius: 2px;
  color: #4B5563;
  background: #F5FAF8;
}

.md-tag--salary {
  color: #1A3C34;
  border-color: #9AC6B8;
  background: #EEF4F2;
  font-weight: 500;
}

.md-auto-dims {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.md-dim-pill {
  display: inline-block;
  padding: 1px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 999px;
}

.md-dim-sem {
  background: #EEF4F2;
  color: #1A3C34;
  border: 0.5px solid #9AC6B8;
}

.md-dim-skill {
  background: #EFF6FF;
  color: #1E40AF;
  border: 0.5px solid #BFDBFE;
}

.md-dim-exp {
  background: #FEF3C7;
  color: #92400E;
  border: 0.5px solid #FCD34D;
}

.md-auto-score {
  font-family: 'Georgia', serif;
  font-size: 22px;
  font-weight: 400;
  flex-shrink: 0;
  min-width: 60px;
  text-align: right;
}
</style>
