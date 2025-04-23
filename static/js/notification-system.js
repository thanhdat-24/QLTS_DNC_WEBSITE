/**
 * Hệ thống thông báo nâng cao - Quản lý và hiển thị thông báo từ database
 */

class NotificationManager {
    constructor() {
        // Khởi tạo container cho dropdown thông báo
        this.setupNotificationDropdown();
        
        // Số lượng thông báo chưa đọc
        this.unreadCount = 0;
        
        // Trạng thái đã load thông báo hay chưa
        this.loaded = false;
        
        // Khởi tạo event listeners
        this.setupEventListeners();
    }
    
    /**
     * Thiết lập dropdown thông báo
     */
    setupNotificationDropdown() {
        // Tìm hoặc tạo container thông báo
        this.notificationElement = document.querySelector('.notifications');
        
        if (!this.notificationElement) {
            console.error('Không tìm thấy phần tử thông báo');
            return;
        }
        
        // Tạo dropdown nếu chưa có
        this.dropdownElement = document.getElementById('notificationDropdown');
        
        if (!this.dropdownElement) {
            this.dropdownElement = document.createElement('div');
            this.dropdownElement.id = 'notificationDropdown';
            this.dropdownElement.className = 'notification-dropdown';
            
            // Thêm HTML cho dropdown
            this.dropdownElement.innerHTML = `
                <div class="notification-header">
                    <h3>Thông báo</h3>
                    <button class="mark-all-read" title="Đánh dấu tất cả là đã đọc">
                        <i class="fas fa-check-double"></i>
                    </button>
                </div>
                <div class="notification-content">
                    <div class="notification-loading">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>Đang tải thông báo...</span>
                    </div>
                </div>
                <div class="notification-footer">
                    <a href="/notifications" class="view-all">Xem tất cả thông báo</a>
                </div>
            `;
            
            // Thêm vào phần tử notifications
            this.notificationElement.appendChild(this.dropdownElement);
        }
        
        // Lấy các phần tử con
        this.notificationContent = this.dropdownElement.querySelector('.notification-content');
        this.notificationLoading = this.dropdownElement.querySelector('.notification-loading');
        this.markAllReadBtn = this.dropdownElement.querySelector('.mark-all-read');
        this.unreadBadge = this.notificationElement.querySelector('.badge');
    }
    
    /**
     * Thiết lập event listeners
     */
    setupEventListeners() {
        // Click vào icon thông báo
        this.notificationElement.addEventListener('click', (e) => {
            // Ngăn sự kiện lan ra document để tránh đóng dropdown ngay lập tức
            e.stopPropagation();
            
            // Hiển thị/ẩn dropdown
            this.toggleDropdown();
        });
        
        // Nút đánh dấu tất cả là đã đọc
        if (this.markAllReadBtn) {
            this.markAllReadBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.markAllAsRead();
            });
        }
        
        // Click bên ngoài để đóng dropdown
        document.addEventListener('click', (e) => {
            if (this.dropdownElement && this.dropdownElement.classList.contains('active') && 
                !this.dropdownElement.contains(e.target)) {
                this.hideDropdown();
            }
        });
    }
    
    /**
     * Hiển thị/ẩn dropdown
     */
    toggleDropdown() {
        if (this.dropdownElement.classList.contains('active')) {
            this.hideDropdown();
        } else {
            this.showDropdown();
        }
    }
    
    /**
     * Hiển thị dropdown và tải thông báo
     */
    showDropdown() {
        this.dropdownElement.classList.add('active');
        
        // Tải thông báo nếu chưa tải
        if (!this.loaded) {
            this.loadNotifications();
        }
    }
    
    /**
     * Ẩn dropdown
     */
    hideDropdown() {
        this.dropdownElement.classList.remove('active');
    }
    
    /**
     * Tải danh sách thông báo từ server
     */
    async loadNotifications() {
        // Hiển thị loading
        this.notificationLoading.style.display = 'flex';
        
        try {
            // Gọi API để lấy thông báo
            const response = await fetch('/api/notifications');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Xử lý và hiển thị thông báo
            this.renderNotifications(data.notifications);
            
            // Cập nhật số lượng thông báo chưa đọc
            this.updateUnreadCount(data.unread_count);
            
            // Đánh dấu đã tải thông báo
            this.loaded = true;
            
        } catch (error) {
            console.error('Lỗi khi tải thông báo:', error);
            this.notificationContent.innerHTML = `
                <div class="notification-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <span>Không thể tải thông báo. Vui lòng thử lại sau.</span>
                </div>
            `;
        } finally {
            // Ẩn loading
            this.notificationLoading.style.display = 'none';
        }
    }
    
    /**
     * Render danh sách thông báo
     * @param {Array} notifications - Mảng thông báo từ API
     */
    renderNotifications(notifications) {
        if (!notifications || notifications.length === 0) {
            this.notificationContent.innerHTML = `
                <div class="notification-empty">
                    <i class="far fa-bell-slash"></i>
                    <span>Không có thông báo mới</span>
                </div>
            `;
            return;
        }
        
        // Tạo HTML cho danh sách thông báo
        const notificationsHtml = notifications.map(notification => `
            <div class="notification-item ${notification.da_doc ? '' : 'unread'}" data-id="${notification.ma_thongbao}">
                <div class="notification-icon ${this.getNotificationIconClass(notification.loai_thongbao)}">
                    <i class="${this.getNotificationIcon(notification.loai_thongbao)}"></i>
                </div>
                <div class="notification-details">
                    <div class="notification-message">${notification.noi_dung}</div>
                    <div class="notification-time">${this.formatTime(notification.ngay_tao)}</div>
                </div>
                <button class="notification-mark-read" title="Đánh dấu đã đọc">
                    <i class="fas fa-check"></i>
                </button>
            </div>
        `).join('');
        
        // Cập nhật nội dung
        this.notificationContent.innerHTML = notificationsHtml;
        
        // Thêm event listeners cho các nút đánh dấu đã đọc
        this.addMarkReadListeners();
    }
    
    /**
     * Thêm event listeners cho các nút đánh dấu đã đọc
     */
    addMarkReadListeners() {
        const markReadButtons = this.notificationContent.querySelectorAll('.notification-mark-read');
        
        markReadButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                
                const notificationItem = button.closest('.notification-item');
                const notificationId = notificationItem.dataset.id;
                
                // Gọi API để đánh dấu đã đọc
                this.markAsRead(notificationId, notificationItem);
            });
        });
        
        // Thêm event click cho notification item để xem chi tiết
        const notificationItems = this.notificationContent.querySelectorAll('.notification-item');
        
        notificationItems.forEach(item => {
            item.addEventListener('click', () => {
                const notificationId = item.dataset.id;
                // Đánh dấu đã đọc và chuyển hướng đến trang chi tiết nếu có
                this.viewNotificationDetail(notificationId, item);
            });
        });
    }
    
    /**
     * Đánh dấu thông báo là đã đọc
     * @param {number} notificationId - ID của thông báo
     * @param {HTMLElement} notificationItem - Phần tử HTML của thông báo
     */
    async markAsRead(notificationId, notificationItem) {
        try {
            // Gọi API để đánh dấu đã đọc
            const response = await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'PUT'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Cập nhật UI
            notificationItem.classList.remove('unread');
            
            // Giảm số lượng thông báo chưa đọc
            if (this.unreadCount > 0) {
                this.updateUnreadCount(this.unreadCount - 1);
            }
            
        } catch (error) {
            console.error('Lỗi khi đánh dấu đã đọc:', error);
        }
    }
    
    /**
     * Xem chi tiết thông báo
     * @param {number} notificationId - ID của thông báo
     * @param {HTMLElement} notificationItem - Phần tử HTML của thông báo
     */
    async viewNotificationDetail(notificationId, notificationItem) {
        // Đánh dấu là đã đọc
        if (notificationItem.classList.contains('unread')) {
            await this.markAsRead(notificationId, notificationItem);
        }
        
        // TODO: Chuyển hướng đến trang chi tiết hoặc hiển thị modal, tùy vào loại thông báo
        // Có thể thực hiện sau khi có API trả về link hoặc data cụ thể
        
        // Đóng dropdown
        this.hideDropdown();
    }
    
    /**
     * Đánh dấu tất cả thông báo là đã đọc
     */
    async markAllAsRead() {
        try {
            // Gọi API để đánh dấu tất cả là đã đọc
            const response = await fetch('/api/notifications/read-all', {
                method: 'PUT'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Cập nhật UI
            const unreadItems = this.notificationContent.querySelectorAll('.notification-item.unread');
            unreadItems.forEach(item => {
                item.classList.remove('unread');
            });
            
            // Cập nhật số lượng thông báo chưa đọc
            this.updateUnreadCount(0);
            
        } catch (error) {
            console.error('Lỗi khi đánh dấu tất cả đã đọc:', error);
        }
    }
    
    /**
     * Cập nhật số lượng thông báo chưa đọc
     * @param {number} count - Số lượng thông báo chưa đọc
     */
    updateUnreadCount(count) {
        this.unreadCount = count;
        
        if (this.unreadBadge) {
            if (count > 0) {
                this.unreadBadge.textContent = count > 99 ? '99+' : count;
                this.unreadBadge.style.display = 'flex';
            } else {
                this.unreadBadge.style.display = 'none';
            }
        }
    }
    
    /**
     * Lấy class icon dựa vào loại thông báo
     * @param {string} type - Loại thông báo
     * @returns {string} CSS class cho icon
     */
    getNotificationIconClass(type) {
        switch (type) {
            case 'update':
                return 'update-icon';
            case 'warning':
                return 'warning-icon';
            case 'error':
                return 'error-icon';
            case 'info':
            default:
                return 'info-icon';
        }
    }
    
    /**
     * Lấy icon dựa vào loại thông báo
     * @param {string} type - Loại thông báo
     * @returns {string} CSS class cho icon
     */
    getNotificationIcon(type) {
        switch (type) {
            case 'update':
                return 'fas fa-sync-alt';
            case 'warning':
                return 'fas fa-exclamation-triangle';
            case 'error':
                return 'fas fa-times-circle';
            case 'info':
            default:
                return 'fas fa-info-circle';
        }
    }
    
    /**
     * Format thời gian thành dạng "vừa xong", "5 phút trước", ...
     * @param {string} dateString - String ISO datetime
     * @returns {string} Thời gian đã format
     */
    formatTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // Số giây
        
        if (diff < 60) {
            return 'Vừa xong';
        } else if (diff < 3600) {
            const minutes = Math.floor(diff / 60);
            return `${minutes} phút trước`;
        } else if (diff < 86400) {
            const hours = Math.floor(diff / 3600);
            return `${hours} giờ trước`;
        } else if (diff < 2592000) {
            const days = Math.floor(diff / 86400);
            return `${days} ngày trước`;
        } else {
            // Format ngày thông thường
            return date.toLocaleDateString('vi-VN');
        }
    }
    
    /**
     * Làm mới danh sách thông báo
     */
    refresh() {
        this.loaded = false;
        if (this.dropdownElement.classList.contains('active')) {
            this.loadNotifications();
        }
    }
}

// Khởi tạo hệ thống thông báo khi DOM đã tải xong
document.addEventListener('DOMContentLoaded', function() {
    // Khởi tạo hệ thống thông báo
    window.notificationManager = new NotificationManager();
});