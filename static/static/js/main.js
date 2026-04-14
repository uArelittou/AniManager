const { createApp, ref, onMounted } = Vue;

createApp({
    setup() {
        // --- 1. 响应式状态管理 (State) ---
        const animeData = ref({});            // 核心数据源
        const currentView = ref('home');      // 路由状态：控制显示主页还是详情页

        // 扫描模态框状态
        const showImportModal = ref(false);
        const scanPath = ref('');
        const isScanning = ref(false);
        const scanMessage = ref('');
        const scanSuccess = ref(true);

        // 详情页状态
        const activeAnimeName = ref('');
        const activeAnimeInfo = ref({});
        const isSelecting = ref(false);

        // 删除确认模态框状态
        const showDeleteModal = ref(false);
        const isDeleting = ref(false);

        // --- 2. 核心业务逻辑 (Methods) ---

        // 初始化加载数据
        const loadData = async () => {
            try {
                const res = await fetch('/api/data');
                animeData.value = await res.json();
            } catch (error) {
                console.error('API请求中断: 获取初始数据失败', error);
            }
        };

        // 唤起本地文件夹选择器
        const selectFolder = async () => {
            isSelecting.value = true;
            try {
                const res = await fetch('/api/select-folder', { method: 'POST' });
                const result = await res.json();

                if (result.status === 'success' && result.path) {
                    scanPath.value = result.path;
                }
            } catch (error) {
                console.error('系统调用中断: 无法唤起文件夹选择', error);
                alert('系统繁忙，请重试');
            } finally {
                isSelecting.value = false;
            }
        };

        // 执行扫描流程
        const startScan = async () => {
            if (!scanPath.value) return;

            isScanning.value = true;
            scanMessage.value = '';

            try {
                const res = await fetch('/api/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: scanPath.value })
                });

                const result = await res.json();

                if (res.ok) {
                    scanSuccess.value = true;
                    scanMessage.value = result.message;
                    animeData.value = result.data; // 更新视图数据

                    // 扫描成功后，延迟 1.5 秒自动关闭模态框
                    setTimeout(() => {
                        showImportModal.value = false;
                        scanPath.value = '';
                        scanMessage.value = '';
                    }, 1500);
                } else {
                    scanSuccess.value = false;
                    scanMessage.value = result.error || '解析引擎返回异常';
                }
            } catch (error) {
                scanSuccess.value = false;
                scanMessage.value = '网络或后端服务异常，请检查终端日志';
            } finally {
                isScanning.value = false;
            }
        };

        // --- 3. 视图导航与交互 ---

        const openAnime = (folderName, info) => {
            activeAnimeName.value = folderName;
            activeAnimeInfo.value = info;
            currentView.value = 'episodes';

            // 压入历史记录，支持浏览器的“后退”按键
            history.pushState({ isEpisodesView: true }, '');
            window.scrollTo(0, 0);
        };

        const goBack = () => {
            currentView.value = 'home';
            window.history.back();
        };

        const playVideo = async (path) => {
            try {
                const res = await fetch('/api/play', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: path })
                });

                if (!res.ok) {
                    const result = await res.json();
                    alert(result.error || '文件系统异常：该文件可能已被移除');
                }
            } catch (error) {
                console.error('服务连接断开', error);
                alert('与本地核心服务的连接丢失，请确认终端是否被关闭！');
            }
        };

        const deleteAnime = () => {
            showDeleteModal.value = true;
        };

        const confirmDelete = async () => {
            isDeleting.value = true;
            
            try {
                const res = await fetch('/api/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: activeAnimeName.value })
                });
                
                const result = await res.json();
                
                if (res.ok) {
                    alert(result.message);
                    // Vue 3 中删除响应式对象属性的正确方法
                    const newData = { ...animeData.value };
                    delete newData[activeAnimeName.value];
                    animeData.value = newData;
                    
                    showDeleteModal.value = false;
                    goBack();
                } else {
                    alert(result.error);
                    showDeleteModal.value = false;
                }
            } catch (error) {
                console.error('删除请求失败', error);
                alert('与服务的连接异常');
                showDeleteModal.value = false;
            } finally {
                isDeleting.value = false;
            }
        };

        // --- 4. 生命周期钩子 ---
        onMounted(() => {
            loadData(); // 挂载时立即请求数据

            // 监听浏览器的物理返回键，同步修改我们的内部视图状态
            window.addEventListener('popstate', (event) => {
                if (!event.state || !event.state.isEpisodesView) {
                    currentView.value = 'home';
                    activeAnimeName.value = '';
                    activeAnimeInfo.value = {};
                }
            });
        });

        // 必须 return 暴露给 HTML 模板使用
        return {
            animeData, currentView,
            showImportModal, scanPath, isScanning, scanMessage, scanSuccess,
            startScan, selectFolder, isSelecting,
            openAnime, activeAnimeName, activeAnimeInfo, goBack,
            playVideo, deleteAnime,
            showDeleteModal, isDeleting, confirmDelete
        };
    }
}).mount('#app');