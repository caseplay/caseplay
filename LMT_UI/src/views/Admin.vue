<template>
  <div class="admin-page">
    <div class="header">
      <h2>后台管理系统</h2>
      <p>管理用户账号、游玩限制与设置</p>
    </div>

    <div class="glass-panel table-container">
      <el-table :data="users" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="账号类型" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.is_admin ? 'danger' : 'success'">
              {{ scope.row.is_admin ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remaining_plays" label="剩余次数" width="120">
          <template #default="scope">
            <strong>{{ scope.row.remaining_plays }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="openEditDialog(scope.row)">管理</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" title="管理用户" width="400px">
      <div v-if="editingUser">
        <el-form label-position="top">
          <el-form-item label="剩余次数">
            <el-input-number v-model="editForm.remaining_plays" :min="0" :max="1000" />
          </el-form-item>
          <el-form-item label="新密码 (可选)">
            <el-input v-model="editForm.password" type="password" placeholder="若不修改请留空" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveUser" :loading="saving">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const users = ref([])
const loading = ref(true)
const dialogVisible = ref(false)
const editingUser = ref(null)
const saving = ref(false)

const editForm = ref({
  remaining_plays: 0,
  password: ''
})

const API_BASE = (import.meta.env.VITE_API_BASE || '/api')

const fetchUsers = async () => {
  const token = localStorage.getItem('token')
  if (!token) return router.push('/login')

  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/admin/users?token=${token}`)
    users.value = res.data
  } catch (err) {
    ElMessage.error(err.response?.data?.error || "用户列表获取失败，需要管理员权限。")
    if (err.response?.status === 403 || err.response?.status === 401) {
      router.push('/')
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchUsers()
})

const openEditDialog = (user) => {
  editingUser.value = user
  editForm.value = {
    remaining_plays: user.remaining_plays,
    password: ''
  }
  dialogVisible.value = true
}

const saveUser = async () => {
  const token = localStorage.getItem('token')
  saving.value = true
  try {
    const payload = {
      token,
      remaining_plays: editForm.value.remaining_plays
    }
    if (editForm.value.password) {
      payload.password = editForm.value.password
    }

    await axios.put(`${API_BASE}/admin/users/${editingUser.value.id}`, payload)
    ElMessage.success("用户资料更新成功")
    dialogVisible.value = false
    await fetchUsers()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || "用户更新失败")
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.admin-page {
  padding: 4rem 2rem;
  max-width: 1000px;
  margin: 0 auto;
}
.header {
  margin-bottom: 2rem;
}
.header h2 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #f8fafc, #94a3b8);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.header p {
  color: var(--text-muted);
}
.table-container {
  padding: 2rem;
}
/* Override Element Plus dark theme variables here if needed */
:global(.el-table) {
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: transparent !important;
  --el-table-header-bg-color: rgba(255,255,255,0.05) !important;
  --el-table-border: 1px solid rgba(255,255,255,0.1) !important;
  --el-table-text-color: var(--text-main) !important;
  --el-table-header-text-color: var(--text-main) !important;
}
:global(.el-dialog) {
  background-color: var(--panel-bg);
  border: 1px solid var(--border);
  backdrop-filter: blur(10px);
}
:global(.el-dialog__title) {
  color: white;
}
:global(.el-form-item__label) {
  color: #ccc;
}
</style>
