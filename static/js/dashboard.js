// 全局变量
let currentTab = 'devices';
let devices = [];
let tasks = [];
let executions = [];
let commandEditor = null;

// 设备状态跟踪
let deviceStatusHistory = {}; // 记录每个设备的状态历史
let deviceFailureCount = {}; // 记录每个设备的连续失败次数

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    bindEventHandlers();
    loadSystemStatus();
    loadCurrentTab();
    
    // 定期刷新系统状态
    setInterval(loadSystemStatus, 30000);
    
    // 定期刷新当前标签页内容
    setInterval(loadCurrentTab, 3000);
}

// 绑定事件处理器
function bindEventHandlers() {
    // 标签页切换 - 桌面端
    document.querySelectorAll('[data-tab]').forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            switchTab(this.getAttribute('data-tab'));
        });
    });
    
    // 移动端导航项点击（使用实际的选择器）
    document.querySelectorAll('.mobile-nav [data-tab]').forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
    
    // 设备表单提交
    document.getElementById('device-form').addEventListener('submit', handleDeviceSubmit);
    
    // 任务表单提交
    document.getElementById('task-form').addEventListener('submit', handleTaskSubmit);
    
    // 执行记录搜索相关事件
    const searchBtn = document.getElementById('search-executions-btn');
    const searchInput = document.getElementById('executions-search');
    const sortBy = document.getElementById('executions-sort-by');
    const sortOrder = document.getElementById('executions-sort-order');
    const limitInput = document.getElementById('executions-limit');
    const deleteBtn = document.getElementById('delete-filtered-executions-btn');
    const cleanupBtn = document.getElementById('cleanup-logs-btn');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', searchExecutions);
    }
    if (searchInput) {
        searchInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                searchExecutions();
            }
        });
        
        // 监听搜索框内容变化，动态更新删除按钮文本
        searchInput.addEventListener('input', updateDeleteButtonText);
    }
    if (sortBy) {
        sortBy.addEventListener('change', loadExecutions);
    }
    if (sortOrder) {
        sortOrder.addEventListener('change', loadExecutions);
    }
    if (limitInput) {
        limitInput.addEventListener('change', loadExecutions);
    }
    if (deleteBtn) {
        deleteBtn.addEventListener('click', deleteFilteredExecutions);
    }
    if (cleanupBtn) {
        cleanupBtn.addEventListener('click', cleanupLogs);
    }
    
    // 初始化CodeMirror编辑器
    initializeCodeEditor();
    
    // 初始化删除按钮文本
    updateDeleteButtonText();
    
}

// 初始化代码编辑器
function initializeCodeEditor() {
    const taskCommandTextarea = document.getElementById('task-command');
    if (taskCommandTextarea && typeof CodeMirror !== 'undefined') {
        commandEditor = CodeMirror.fromTextArea(taskCommandTextarea, {
            mode: 'shell',
            lineNumbers: true,
            lineWrapping: true,
            autofocus: false,
            tabSize: 2,
            indentWithTabs: false,
            theme: 'default',
            extraKeys: {
                'Ctrl-Space': 'autocomplete'
            }
        });
        
        // 设置编辑器高度
        commandEditor.setSize(null, 120);
    }
}

// 切换标签页
function switchTab(tabName) {
    // 更新桌面端导航状态
    document.querySelectorAll('.desktop-sidebar [data-tab]').forEach(tab => {
        tab.classList.remove('active');
    });
    const desktopTab = document.querySelector(`.desktop-sidebar [data-tab="${tabName}"]`);
    if (desktopTab) {
        desktopTab.classList.add('active');
    }
    
    // 更新移动端导航状态
    document.querySelectorAll('.mobile-nav [data-tab]').forEach(tab => {
        tab.classList.remove('active');
    });
    const mobileTab = document.querySelector(`.mobile-nav [data-tab="${tabName}"]`);
    if (mobileTab) {
        mobileTab.classList.add('active');
    }
    
    // 隐藏所有内容区域
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('d-none');
    });
    
    // 显示当前标签页内容
    document.getElementById(`${tabName}-content`).classList.remove('d-none');
    
    currentTab = tabName;
    loadCurrentTab();
}

// 加载当前标签页内容
function loadCurrentTab() {
    // 先停止任何现有的自动刷新
    stopSystemInfoRefresh();
    
    switch(currentTab) {
        case 'devices':
            loadDevices();
            break;
        case 'tasks':
            loadTasks();
            break;
        case 'executions':
            loadExecutions();
            break;
        case 'system':
            loadSystemInfo();
            startSystemInfoRefresh(); // 启动系统状态自动刷新
            break;
    }
}

// API请求封装
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API请求失败:', error);
        showAlert('请求失败: ' + error.message, 'danger');
        throw error;
    }
}

// 加载系统状态
async function loadSystemStatus() {
    try {
        const response = await apiRequest('/api/status');
        if (response.success) {
            updateSystemStatus(response.data);
        }
    } catch (error) {
        document.getElementById('system-status').innerHTML = 
            '<i class="bi bi-circle-fill text-danger"></i> 系统离线';
    }
}

// 更新系统状态显示
function updateSystemStatus(status) {
    const statusElement = document.getElementById('system-status');
    if (status.scheduler_running) {
        statusElement.innerHTML = 
            `<i class="bi bi-circle-fill text-success"></i> 
             调度器运行中 (${status.active_jobs}个活动任务)`;
    } else {
        statusElement.innerHTML = 
            '<i class="bi bi-circle-fill text-warning"></i> 调度器已停止';
    }
}

// WOL设备管理

// 格式化设备地址显示
function formatDeviceAddress(device) {
    // 使用后端计算的优化显示地址
    const displayAddress = device.display_address || '-';
    
    if (displayAddress === '-') {
        return '<span class="text-muted">-</span>';
    }
    
    // 如果是mDNS主机名，添加特殊样式和图标
    if (device.is_mdns) {
        return `<span class="text-success" title="mDNS主机名">
            <i class="bi bi-broadcast"></i> ${displayAddress}
        </span>`;
    }
    
    // 检查是否为主机名（非IP地址）
    const isIP = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(displayAddress);
    if (!isIP) {
        // 普通主机名
        return `<span class="text-info" title="主机名">
            <i class="bi bi-hdd-network"></i> ${displayAddress}
        </span>`;
    } else {
        // IP地址
        return `<span class="text-primary" title="IP地址">
            <i class="bi bi-router"></i> ${displayAddress}
        </span>`;
    }
}

async function loadDevices() {
    try {
        const response = await apiRequest('/api/devices');
        if (response.success) {
            devices = response.data;
            renderDevicesTable();
        }
    } catch (error) {
        console.error('加载设备失败:', error);
    }
}

function renderDevicesTable() {
    const tbody = document.querySelector('#devices-table tbody');
    tbody.innerHTML = '';
    
    devices.forEach(device => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="device-status unknown" id="status-${device.id}"></span></td>
            <td>${device.name}</td>
            <td>${formatDeviceAddress(device)}</td>
            <td><code>${device.mac_address}</code></td>
            <td>${device.description || '-'}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-success" onclick="wakeDevice(${device.id})" title="唤醒">
                        <i class="bi bi-power"></i>
                    </button>
                    <button class="btn btn-info" onclick="pingDevice(${device.id})" title="Ping">
                        <i class="bi bi-wifi"></i>
                    </button>
                    <button class="btn btn-primary" onclick="editDevice(${device.id})" title="编辑">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-danger" onclick="deleteDevice(${device.id})" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
        
        // 检查设备状态
        checkDeviceStatus(device);
    });
}

async function checkDeviceStatus(device) {
    try {
        const response = await apiRequest(`/api/wol/ping/${device.id}`, {method: 'POST'});
        const statusElement = document.getElementById(`status-${device.id}`);
        if (!statusElement) return;
        
        const deviceId = device.id;
        const currentOnline = response.data.online;
        
        // 初始化设备状态跟踪
        if (!deviceStatusHistory[deviceId]) {
            deviceStatusHistory[deviceId] = 'unknown';
            deviceFailureCount[deviceId] = 0;
        }
        
        // 获取之前的状态
        const previousStatus = deviceStatusHistory[deviceId];
        let newStatus = currentOnline ? 'online' : 'offline';
        
        if (currentOnline) {
            // 设备在线：重置失败计数，直接更新为在线
            deviceFailureCount[deviceId] = 0;
            deviceStatusHistory[deviceId] = 'online';
            statusElement.className = 'device-status online';
            statusElement.title = '在线';
        } else {
            // 设备离线：增加失败计数
            deviceFailureCount[deviceId]++;
            
            if (previousStatus === 'online') {
                // 从在线变为离线：需要连续3次失败才显示为离线
                if (deviceFailureCount[deviceId] >= 3) {
                    deviceStatusHistory[deviceId] = 'offline';
                    statusElement.className = 'device-status offline';
                    statusElement.title = '离线';
                } else {
                    // 保持在线状态，但显示为pending表示正在检测
                    statusElement.className = 'device-status pending';
                    statusElement.title = `检测中 (${deviceFailureCount[deviceId]}/3)`;
                }
            } else if (previousStatus === 'unknown') {
                // 初次检测到离线：直接显示为离线
                deviceStatusHistory[deviceId] = 'offline';
                statusElement.className = 'device-status offline';
                statusElement.title = '离线';
            } else {
                // 已经是离线状态：保持离线
                statusElement.className = 'device-status offline';
                statusElement.title = '离线';
            }
        }
        
    } catch (error) {
        console.error('检查设备状态失败:', error);
        // 网络错误时显示为未知状态
        const statusElement = document.getElementById(`status-${device.id}`);
        if (statusElement) {
            statusElement.className = 'device-status unknown';
            statusElement.title = '检测失败';
        }
    }
}

async function wakeDevice(deviceId) {
    try {
        const response = await apiRequest('/api/wol/wake', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({device_id: deviceId})
        });
        
        if (response.success) {
            showAlert('WOL包发送成功', 'success');
            setTimeout(() => checkDeviceStatus(devices.find(d => d.id === deviceId)), 3000);
        } else {
            showAlert('WOL包发送失败: ' + response.message, 'danger');
        }
    } catch (error) {
        console.error('WOL唤醒错误:', error);
        showAlert('唤醒设备失败', 'danger');
    }
}

async function pingDevice(deviceId) {
    try {
        const response = await apiRequest(`/api/wol/ping/${deviceId}`, {method: 'POST'});
        if (response.success) {
            const status = response.data.online ? '在线' : '离线';
            const alertType = response.data.online ? 'success' : 'warning';
            showAlert(`设备状态: ${status}`, alertType);
            
            const statusElement = document.getElementById(`status-${deviceId}`);
            if (statusElement) {
                statusElement.className = `device-status ${response.data.online ? 'online' : 'offline'}`;
            }
        }
    } catch (error) {
        showAlert('Ping设备失败', 'danger');
    }
}

function editDevice(deviceId) {
    const device = devices.find(d => d.id === deviceId);
    if (device) {
        document.getElementById('device-id').value = device.id;
        document.getElementById('device-name').value = device.name;
        document.getElementById('device-hostname').value = device.hostname || '';
        document.getElementById('device-ip').value = device.ip_address || '';
        document.getElementById('device-mac').value = device.mac_address;
        document.getElementById('device-description').value = device.description || '';
        
        new bootstrap.Modal(document.getElementById('deviceModal')).show();
    }
}

async function deleteDevice(deviceId) {
    if (confirm('确定要删除这个设备吗？')) {
        try {
            const response = await apiRequest(`/api/devices/${deviceId}`, {method: 'DELETE'});
            if (response.success) {
                showAlert('设备删除成功', 'success');
                loadDevices();
            }
        } catch (error) {
            showAlert('删除设备失败', 'danger');
        }
    }
}

async function handleDeviceSubmit(e) {
    e.preventDefault();
    
    const deviceId = document.getElementById('device-id').value;
    const deviceData = {
        name: document.getElementById('device-name').value,
        hostname: document.getElementById('device-hostname').value,
        ip_address: document.getElementById('device-ip').value,
        mac_address: document.getElementById('device-mac').value,
        description: document.getElementById('device-description').value
    };
    
    try {
        let response;
        if (deviceId) {
            response = await apiRequest(`/api/devices/${deviceId}`, {
                method: 'PUT',
                body: JSON.stringify(deviceData)
            });
        } else {
            response = await apiRequest('/api/devices', {
                method: 'POST',
                body: JSON.stringify(deviceData)
            });
        }
        
        if (response.success) {
            showAlert(deviceId ? '设备更新成功' : '设备创建成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('deviceModal')).hide();
            document.getElementById('device-form').reset();
            loadDevices();
        } else {
            showAlert('操作失败: ' + response.message, 'danger');
        }
    } catch (error) {
        showAlert('操作失败', 'danger');
    }
}

// 定时任务管理
async function loadTasks() {
    try {
        const response = await apiRequest('/api/tasks');
        if (response.success) {
            tasks = response.data;
            renderTasksTable();
        }
    } catch (error) {
        console.error('加载任务失败:', error);
    }
}

function renderTasksTable() {
    const tbody = document.querySelector('#tasks-table tbody');
    tbody.innerHTML = '';
    
    tasks.forEach(task => {
        const row = document.createElement('tr');
        const statusBadge = task.enabled ? 
            '<span class="badge bg-success status-badge">启用</span>' : 
            '<span class="badge bg-secondary status-badge">禁用</span>';
        
        const lastRun = task.last_run_at ? 
            new Date(task.last_run_at).toLocaleString() : '-';
        const nextRun = task.next_run_at ? 
            new Date(task.next_run_at).toLocaleString() : '-';
        
        const schedule = task.cron_expression || 
            (task.interval_seconds ? `每${task.interval_seconds}秒` : '-');
        
        row.innerHTML = `
            <td>${statusBadge}</td>
            <td>
                <strong>${task.name}</strong>
                ${task.description ? `<br><small class="text-muted">${task.description}</small>` : ''}
            </td>
            <td><span class="badge bg-info">${task.task_type}</span></td>
            <td><code>${schedule}</code></td>
            <td><small>${lastRun}</small></td>
            <td><small>${nextRun}</small></td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-success" onclick="executeTask(${task.id})" title="立即执行">
                        <i class="bi bi-play"></i>
                    </button>
                    <button class="btn btn-warning" onclick="toggleTask(${task.id})" title="启用/禁用">
                        <i class="bi bi-toggle-${task.enabled ? 'on' : 'off'}"></i>
                    </button>
                    <button class="btn btn-info" onclick="viewTaskLogs(${task.id})" title="查看日志">
                        <i class="bi bi-file-text"></i>
                    </button>
                    <button class="btn btn-primary" onclick="editTask(${task.id})" title="编辑">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-danger" onclick="deleteTask(${task.id})" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function executeTask(taskId) {
    try {
        const response = await apiRequest(`/api/tasks/${taskId}/execute`, {method: 'POST'});
        if (response.success) {
            showAlert('任务已开始执行', 'success');
            setTimeout(loadTasks, 2000);
        }
    } catch (error) {
        showAlert('执行任务失败', 'danger');
    }
}

async function toggleTask(taskId) {
    try {
        const response = await apiRequest(`/api/tasks/${taskId}/toggle`, {method: 'POST'});
        if (response.success) {
            showAlert(response.message, 'success');
            loadTasks();
        }
    } catch (error) {
        showAlert('切换任务状态失败', 'danger');
    }
}

async function viewTaskLogs(taskId) {
    try {
        const response = await apiRequest(`/api/tasks/${taskId}/executions`);
        if (response.success) {
            renderExecutionLogs(response.data);
            new bootstrap.Modal(document.getElementById('logModal')).show();
        }
    } catch (error) {
        showAlert('加载执行日志失败', 'danger');
    }
}

function renderExecutionLogs(executions) {
    const logContent = document.getElementById('log-content');
    if (executions.length === 0) {
        logContent.innerHTML = '<div class="text-center text-muted">暂无执行记录</div>';
        return;
    }
    
    let html = '';
    executions.forEach(exec => {
        const statusClass = getStatusClass(exec.status);
        const duration = exec.duration_seconds ? `${exec.duration_seconds.toFixed(2)}秒` : '-';
        const startTime = exec.started_at ? new Date(exec.started_at).toLocaleString() : '-';
        
        html += `
            <div class="log-execution-item">
                <div class="log-execution-header">
                    <h6 class="mb-0">执行 #${exec.id}</h6>
                    <span class="badge ${statusClass}">${exec.status}</span>
                </div>
                <div class="log-execution-meta">
                    <div class="row">
                        <div class="col-sm-6">
                            <strong>开始时间:</strong> ${startTime}<br>
                            <strong>耗时:</strong> ${duration}<br>
                            <strong>退出码:</strong> ${exec.exit_code !== null ? exec.exit_code : '-'}
                        </div>
                        <div class="col-sm-6">
                            <strong>PID:</strong> ${exec.pid || '-'}<br>
                            <strong>命令:</strong><br><pre class="bg-light p-2 mt-1" style="font-size: 0.8rem; line-height: 1.3; margin-bottom: 4px; white-space: pre-wrap; word-break: break-all;">${exec.command}</pre>
                        </div>
                    </div>
                </div>
                ${exec.stdout ? `<div class="log-execution-output"><strong>输出:</strong><pre class="bg-light p-1 mt-1" style="font-size: 0.75rem; line-height: 1.2; margin-bottom: 4px;">${exec.stdout}</pre></div>` : ''}
                ${exec.stderr ? `<div class="log-execution-output"><strong>错误:</strong><pre class="bg-danger text-white p-1 mt-1" style="font-size: 0.75rem; line-height: 1.2; margin-bottom: 4px;">${exec.stderr}</pre></div>` : ''}
                ${exec.error_message ? `<div class="log-execution-output"><strong>错误信息:</strong><div class="text-danger" style="font-size: 0.8rem;">${exec.error_message}</div></div>` : ''}
            </div>
        `;
    });
    
    logContent.innerHTML = html;
}

function createNewTask() {
    // 清空当前任务数据
    window.currentEditingTask = null;
    
    // 重置表单字段
    document.getElementById('task-id').value = '';
    document.getElementById('task-name').value = '';
    document.getElementById('task-type').value = 'shell';
    document.getElementById('task-command').value = '';
    document.getElementById('task-description').value = '';
    document.getElementById('task-cron').value = '';
    document.getElementById('task-interval').value = '';
    document.getElementById('task-timeout').value = '300';
    document.getElementById('task-enabled').checked = true;
    
    // 如果CodeMirror已初始化，也清空编辑器内容
    if (commandEditor) {
        commandEditor.setValue('');
    }
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('taskModal'));
    modal.show();
}

function editTask(taskId) {
    const task = tasks.find(t => t.id === taskId);
    if (task) {
        // 存储当前任务数据供模态框事件使用
        window.currentEditingTask = task;
        
        document.getElementById('task-id').value = task.id;
        document.getElementById('task-name').value = task.name;
        document.getElementById('task-type').value = task.task_type;
        
        // 先设置普通文本框的值
        document.getElementById('task-command').value = task.command || '';
        
        document.getElementById('task-description').value = task.description || '';
        document.getElementById('task-cron').value = task.cron_expression || '';
        document.getElementById('task-interval').value = task.interval_seconds || '';
        document.getElementById('task-timeout').value = task.timeout_seconds;
        document.getElementById('task-enabled').checked = task.enabled;
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('taskModal'));
        modal.show();
    }
}

async function deleteTask(taskId) {
    if (confirm('确定要删除这个任务吗？相关的执行记录也会被删除。')) {
        try {
            const response = await apiRequest(`/api/tasks/${taskId}`, {method: 'DELETE'});
            if (response.success) {
                showAlert('任务删除成功', 'success');
                loadTasks();
            }
        } catch (error) {
            showAlert('删除任务失败', 'danger');
        }
    }
}

async function handleTaskSubmit(e) {
    e.preventDefault();
    
    const taskId = document.getElementById('task-id').value;
    
    // 从CodeMirror编辑器或普通文本框获取命令内容
    let command = '';
    if (commandEditor) {
        command = commandEditor.getValue();
    } else {
        command = document.getElementById('task-command').value;
    }
    
    // 手动验证必填字段（避免浏览器聚焦到隐藏的textarea）
    const taskName = document.getElementById('task-name').value.trim();
    if (!taskName) {
        showAlert('请输入任务名称', 'warning');
        document.getElementById('task-name').focus();
        return;
    }
    
    if (!command || command.trim() === '') {
        showAlert('请输入任务命令', 'warning');
        if (commandEditor) {
            commandEditor.focus();
        } else {
            document.getElementById('task-command').focus();
        }
        return;
    }
    
    const taskData = {
        name: taskName,
        task_type: document.getElementById('task-type').value,
        command: command.trim(),
        description: document.getElementById('task-description').value,
        cron_expression: document.getElementById('task-cron').value || null,
        interval_seconds: document.getElementById('task-interval').value ? 
            parseInt(document.getElementById('task-interval').value) : null,
        timeout_seconds: parseInt(document.getElementById('task-timeout').value),
        max_retries: 0,
        enabled: document.getElementById('task-enabled').checked
    };
    
    // Debug logging
    console.log('Task data being sent:', JSON.stringify(taskData, null, 2));
    console.log('Task ID:', taskId);
    
    try {
        let response;
        if (taskId) {
            console.log('Sending PUT request to update task');
            response = await apiRequest(`/api/tasks/${taskId}`, {
                method: 'PUT',
                body: JSON.stringify(taskData)
            });
        } else {
            console.log('Sending POST request to create task');
            response = await apiRequest('/api/tasks', {
                method: 'POST',
                body: JSON.stringify(taskData)
            });
        }
        
        if (response.success) {
            showAlert(taskId ? '任务更新成功' : '任务创建成功', 'success');
            bootstrap.Modal.getInstance(document.getElementById('taskModal')).hide();
            document.getElementById('task-form').reset();
            loadTasks();
        } else {
            showAlert('操作失败: ' + response.message, 'danger');
        }
    } catch (error) {
        showAlert('操作失败', 'danger');
    }
}


// 执行记录管理
async function loadExecutions() {
    try {
        const searchValue = document.getElementById('executions-search')?.value || '';
        const sortBy = document.getElementById('executions-sort-by')?.value || 'created_at';
        const sortOrder = document.getElementById('executions-sort-order')?.value || 'desc';
        const limit = document.getElementById('executions-limit')?.value || 100;
        
        const params = new URLSearchParams({
            limit: limit,
            sort_by: sortBy,
            sort_order: sortOrder
        });
        
        if (searchValue) {
            params.append('search', searchValue);
        }
        
        const response = await apiRequest(`/api/executions?${params.toString()}`);
        if (response.success) {
            executions = response.data;
            renderExecutionsTable();
        }
    } catch (error) {
        console.error('加载执行记录失败:', error);
    }
}

async function searchExecutions() {
    await loadExecutions();
}

// 更新删除按钮文本
function updateDeleteButtonText() {
    const searchValue = document.getElementById('executions-search')?.value || '';
    const deleteBtn = document.getElementById('delete-btn-text');
    
    if (deleteBtn) {
        if (searchValue.trim()) {
            deleteBtn.textContent = '删除结果';
            document.getElementById('delete-filtered-executions-btn').title = '删除搜索结果';
        } else {
            deleteBtn.textContent = '清空所有';
            document.getElementById('delete-filtered-executions-btn').title = '清空所有记录';
        }
    }
}

async function deleteFilteredExecutions() {
    const searchValue = document.getElementById('executions-search')?.value || '';
    const deleteBtn = document.getElementById('delete-btn-text');
    const isSearchMode = searchValue.trim() !== '';
    
    if (!isSearchMode) {
        // 搜索框为空时，清空所有记录
        if (!confirm('确定要清空所有执行记录吗？这将无法撤销！')) {
            return;
        }
    } else {
        // 搜索框不为空时，删除搜索结果
        if (!confirm(`确定要删除搜索"${searchValue}"的所有匹配记录吗？这将无法撤销！`)) {
            return;
        }
    }
    
    try {
        let url = '/api/executions';
        const requestOptions = {
            method: 'DELETE'
        };
        
        if (isSearchMode) {
            // 搜索模式下通过查询参数传递搜索条件
            const params = new URLSearchParams();
            params.append('search', searchValue);
            url = `/api/executions?${params.toString()}`;
        }
        // 如果不是搜索模式，直接请求 /api/executions (无参数) 将删除所有记录
        
        const response = await apiRequest(url, requestOptions);
        
        if (response.success) {
            showAlert(response.message, 'success');
            await loadExecutions();
            // 如果是清空所有模式，清空搜索框并更新按钮文本
            if (!isSearchMode) {
                document.getElementById('executions-search').value = '';
                updateDeleteButtonText();
            }
        } else {
            showAlert('删除失败: ' + response.message, 'danger');
        }
    } catch (error) {
        showAlert('删除执行记录失败', 'danger');
    }
}

function renderExecutionsTable() {
    const tbody = document.querySelector('#executions-table tbody');
    tbody.innerHTML = '';
    
    executions.forEach(execution => {
        const row = document.createElement('tr');
        const statusBadge = `<span class="badge ${getStatusClass(execution.status)} status-badge">${execution.status}</span>`;
        const startTime = execution.started_at ? 
            new Date(execution.started_at).toLocaleString() : '-';
        const duration = execution.duration_seconds ? 
            `${execution.duration_seconds.toFixed(2)}秒` : '-';
        
        row.innerHTML = `
            <td>${execution.task_name}</td>
            <td>${statusBadge}</td>
            <td><small>${startTime}</small></td>
            <td><small>${duration}</small></td>
            <td><code>${execution.exit_code !== null ? execution.exit_code : '-'}</code></td>
            <td>
                <button class="btn btn-sm btn-info" onclick="viewExecutionLog(${execution.id})" title="查看日志">
                    <i class="bi bi-file-text"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function viewExecutionLog(executionId) {
    const execution = executions.find(e => e.id === executionId);
    if (execution) {
        renderExecutionLogs([execution]);
        new bootstrap.Modal(document.getElementById('logModal')).show();
    }
}

// 系统信息
async function loadSystemInfo() {
    try {
        const response = await apiRequest('/api/status');
        if (response.success && response.data) {
            renderSystemInfo(response.data);
        } else {
            console.error('系统状态API响应错误:', response);
            const systemInfo = document.getElementById('system-info');
            if (systemInfo) {
                systemInfo.innerHTML = '<div class="alert alert-danger">系统状态加载失败，请检查服务器连接或刷新页面重试</div>';
            }
        }
    } catch (error) {
        console.error('加载系统信息失败:', error);
        const systemInfo = document.getElementById('system-info');
        if (systemInfo) {
            systemInfo.innerHTML = '<div class="alert alert-danger">系统状态加载异常，请检查网络连接或刷新页面重试</div>';
        }
    }
}

// 自动刷新系统状态
let systemInfoRefreshInterval;

function startSystemInfoRefresh() {
    // 清除现有的定时器
    if (systemInfoRefreshInterval) {
        clearInterval(systemInfoRefreshInterval);
    }
    
    // 只在系统状态页面启动自动刷新
    if (currentTab === 'status') {
        systemInfoRefreshInterval = setInterval(() => {
            if (currentTab === 'status') {
                loadSystemInfo();
            } else {
                // 如果不在系统状态页面，停止刷新
                stopSystemInfoRefresh();
            }
        }, 5000); // 每5秒刷新一次
    }
}

function stopSystemInfoRefresh() {
    if (systemInfoRefreshInterval) {
        clearInterval(systemInfoRefreshInterval);
        systemInfoRefreshInterval = null;
    }
}

function renderSystemInfo(status) {
    const systemInfo = document.getElementById('system-info');
    
    // 检查数据结构是否正确
    if (!status || !status.server || !status.system || !status.scheduler || !status.database) {
        console.error('系统状态数据结构不完整:', status);
        systemInfo.innerHTML = '<div class="alert alert-warning">系统状态数据加载不完整，请刷新页面重试</div>';
        return;
    }
    
    // 格式化字节单位
    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // 格式化网络流量
    function formatNetworkBytes(bytes) {
        const gb = bytes / (1024 * 1024 * 1024);
        if (gb >= 1) return gb.toFixed(2) + ' GB';
        const mb = bytes / (1024 * 1024);
        if (mb >= 1) return mb.toFixed(2) + ' MB';
        const kb = bytes / 1024;
        return kb.toFixed(2) + ' KB';
    }
    
    // 获取进度条颜色
    function getProgressBarColor(percent) {
        if (percent < 50) return 'bg-success';
        if (percent < 80) return 'bg-warning';
        return 'bg-danger';
    }
    
    systemInfo.innerHTML = `
        <!-- 服务器基础信息 -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="bi bi-server"></i> 服务器信息</h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>状态:</strong> 
                                    <span class="badge bg-success">
                                        <i class="bi bi-circle-fill"></i> ${status.server.status}
                                    </span>
                                </p>
                                <p><strong>运行时间:</strong> ${status.server.uptime}</p>
                                <p><strong>版本:</strong> ${status.server.version}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Python版本:</strong> ${status.server.python_version}</p>
                                <p><strong>系统平台:</strong> ${status.server.platform}</p>
                                <p><strong>架构:</strong> ${status.server.architecture}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 系统资源监控 -->
        <div class="row mb-4">
            <!-- CPU使用率 -->
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="bi bi-cpu"></i> CPU使用率</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span>使用率</span>
                            <span><strong>${status.system.cpu_usage}%</strong></span>
                        </div>
                        <div class="progress mb-2" style="height: 20px;">
                            <div class="progress-bar ${getProgressBarColor(status.system.cpu_usage)}" 
                                 style="width: ${status.system.cpu_usage}%">
                                ${status.system.cpu_usage}%
                            </div>
                        </div>
                        <small class="text-muted">核心数: ${status.system.cpu_count}</small>
                    </div>
                </div>
            </div>
            
            <!-- 内存使用率 -->
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="bi bi-memory"></i> 内存使用率</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span>已使用</span>
                            <span><strong>${formatBytes(status.system.memory.used)} / ${formatBytes(status.system.memory.total)}</strong></span>
                        </div>
                        <div class="progress mb-2" style="height: 20px;">
                            <div class="progress-bar ${getProgressBarColor(status.system.memory.percent)}" 
                                 style="width: ${status.system.memory.percent}%">
                                ${status.system.memory.percent}%
                            </div>
                        </div>
                        <small class="text-muted">可用: ${formatBytes(status.system.memory.available)}</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <!-- 磁盘使用率 -->
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="bi bi-hdd"></i> 磁盘使用率</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span>已使用</span>
                            <span><strong>${formatBytes(status.system.disk.used)} / ${formatBytes(status.system.disk.total)}</strong></span>
                        </div>
                        <div class="progress mb-2" style="height: 20px;">
                            <div class="progress-bar ${getProgressBarColor(status.system.disk.percent)}" 
                                 style="width: ${status.system.disk.percent}%">
                                ${status.system.disk.percent}%
                            </div>
                        </div>
                        <small class="text-muted">可用: ${formatBytes(status.system.disk.free)}</small>
                    </div>
                </div>
            </div>
            
            <!-- 网络流量 -->
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="bi bi-wifi"></i> 网络流量</h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <div class="text-center">
                                    <i class="bi bi-arrow-up text-success fs-4"></i>
                                    <p class="mb-0"><strong>${formatNetworkBytes(status.system.network.bytes_sent)}</strong></p>
                                    <small class="text-muted">发送</small>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="text-center">
                                    <i class="bi bi-arrow-down text-info fs-4"></i>
                                    <p class="mb-0"><strong>${formatNetworkBytes(status.system.network.bytes_recv)}</strong></p>
                                    <small class="text-muted">接收</small>
                                </div>
                            </div>
                        </div>
                        <hr>
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">发送包: ${status.system.network.packets_sent.toLocaleString()}</small>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">接收包: ${status.system.network.packets_recv.toLocaleString()}</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 服务状态 -->
        <div class="row">
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="bi bi-gear"></i> 调度器状态</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span>状态:</span>
                            <span class="badge ${status.scheduler.running ? 'bg-success' : 'bg-danger'}">
                                <i class="bi bi-${status.scheduler.running ? 'play' : 'stop'}-fill"></i>
                                ${status.scheduler.running ? '运行中' : '已停止'}
                            </span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span>活动任务:</span>
                            <span><strong>${status.scheduler.active_jobs}</strong></span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="bi bi-database"></i> 数据统计</h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <div class="text-center">
                                    <h5 class="text-primary">${status.database.device_count}</h5>
                                    <small class="text-muted">设备</small>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="text-center">
                                    <h5 class="text-success">${status.database.enabled_task_count}/${status.database.task_count}</h5>
                                    <small class="text-muted">启用任务</small>
                                </div>
                            </div>
                        </div>
                        <hr>
                        <div class="text-center">
                            <small class="text-muted">执行记录: ${status.database.execution_count}</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 系统维护
async function cleanupLogs() {
    if (confirm('确定要清理30天前的执行记录吗？')) {
        try {
            const response = await apiRequest('/api/maintenance/cleanup', {method: 'POST'});
            if (response.success) {
                showAlert('日志清理成功', 'success');
                if (currentTab === 'executions') {
                    loadExecutions();
                }
            }
        } catch (error) {
            showAlert('日志清理失败', 'danger');
        }
    }
}

// 工具函数
function getStatusClass(status) {
    const statusClasses = {
        'pending': 'bg-secondary',
        'running': 'bg-primary',
        'completed': 'bg-success',
        'failed': 'bg-danger',
        'cancelled': 'bg-warning'
    };
    return statusClasses[status] || 'bg-secondary';
}

function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    // 自动隐藏
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        if (alerts.length > 0) {
            alerts[alerts.length - 1].remove();
        }
    }, 5000);
}

// 清空模态框表单
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('shown.bs.modal', function () {
        // 如果是任务模态框且有正在编辑的任务，设置CodeMirror内容
        if (this.id === 'taskModal' && window.currentEditingTask && commandEditor) {
            commandEditor.setValue(window.currentEditingTask.command || '');
            commandEditor.refresh(); // 强制刷新显示
            commandEditor.focus(); // 设置焦点
        }
    });
    
    modal.addEventListener('hidden.bs.modal', function () {
        const forms = this.querySelectorAll('form');
        forms.forEach(form => form.reset());
        
        // 清空隐藏的ID字段
        const idFields = this.querySelectorAll('input[type="hidden"]');
        idFields.forEach(field => field.value = '');
        
        // 如果是任务模态框，清空CodeMirror编辑器和当前编辑任务
        if (this.id === 'taskModal') {
            if (commandEditor) {
                commandEditor.setValue('');
            }
            window.currentEditingTask = null;
        }
    });
});