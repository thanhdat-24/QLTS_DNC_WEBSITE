/**
 * AssetManager - Hệ thống quản lý tài sản
 * @version 1.0.0
 */

// DOM Elements
let searchInput;
let filterButtons;
let filterMenus;
let filterOptions;
let clearFiltersBtn;
let productCards;
let emptyState;
let productList;

/**
 * Hệ thống thông báo
 * Hiển thị thông báo trong quá trình người dùng tương tác
 */
class NotificationSystem {
    constructor() {
        this.notifications = [];
        
        // Tạo container chứa thông báo nếu chưa tồn tại
        this.container = document.getElementById('notification-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.className = 'notification-container';
            document.body.appendChild(this.container);
        }
        
        // Thêm styles nếu chưa có trong document
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                .notification-container {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1000;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }
                .notification {
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    padding: 15px;
                    width: 300px;
                    transform: translateX(400px);
                    transition: transform 0.3s ease;
                    display: flex;
                    align-items: flex-start;
                    gap: 10px;
                }
                .notification.show {
                    transform: translateX(0);
                }
                .notification-icon {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                }
                .notification-success .notification-icon {
                    background-color: rgba(76, 175, 80, 0.15);
                    color: #4caf50;
                }
                .notification-error .notification-icon {
                    background-color: rgba(244, 67, 54, 0.15);
                    color: #f44336;
                }
                .notification-warning .notification-icon {
                    background-color: rgba(255, 152, 0, 0.15);
                    color: #ff9800;
                }
                .notification-info .notification-icon {
                    background-color: rgba(33, 150, 243, 0.15);
                    color: #2196f3;
                }
                .notification-content {
                    flex: 1;
                }
                .notification-title {
                    font-weight: 600;
                    margin-bottom: 3px;
                }
                .notification-message {
                    font-size: 13px;
                    color: #666;
                }
                .notification-close {
                    background: none;
                    border: none;
                    font-size: 16px;
                    cursor: pointer;
                    color: #999;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    transition: all 0.2s ease;
                }
                .notification-close:hover {
                    background-color: #f1f3f5;
                    color: #333;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Tạo một thông báo mới
     * @param {string} type - Loại thông báo (success, error, warning, info)
     * @param {string} title - Tiêu đề thông báo
     * @param {string} message - Nội dung thông báo
     * @param {number} duration - Thời gian hiển thị (ms), mặc định 3000ms
     */
    createNotification(type, title, message, duration = 3000) {
        const id = 'notification-' + Date.now();
        
        // Tạo icon phù hợp với loại thông báo
        let icon = '';
        switch(type) {
            case 'success':
                icon = '<i class="fas fa-check"></i>';
                break;
            case 'error':
                icon = '<i class="fas fa-times"></i>';
                break;
            case 'warning':
                icon = '<i class="fas fa-exclamation"></i>';
                break;
            case 'info':
            default:
                icon = '<i class="fas fa-info"></i>';
                break;
        }
        
        // Tạo HTML cho thông báo
        const notificationElement = document.createElement('div');
        notificationElement.className = `notification notification-${type}`;
        notificationElement.id = id;
        notificationElement.innerHTML = `
            <div class="notification-icon">${icon}</div>
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close"><i class="fas fa-times"></i></button>
        `;
        
        // Thêm vào container
        this.container.appendChild(notificationElement);
        
        // Thêm event listener cho nút đóng
        notificationElement.querySelector('.notification-close').addEventListener('click', () => {
            this.removeNotification(id);
        });
        
        // Hiện thông báo với animation
        setTimeout(() => {
            notificationElement.classList.add('show');
        }, 10);
        
        // Tự động ẩn sau thời gian duration
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(id);
            }, duration);
        }
        
        // Lưu vào danh sách thông báo
        this.notifications.push({
            id,
            element: notificationElement
        });
        
        return id;
    }
    
    /**
     * Xóa một thông báo
     * @param {string} id - ID của thông báo cần xóa
     */
    removeNotification(id) {
        const notification = document.getElementById(id);
        if (notification) {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
                this.notifications = this.notifications.filter(n => n.id !== id);
            }, 300);
        }
    }
    
    /**
     * Hiển thị thông báo thành công
     */
    success(title, message, duration) {
        return this.createNotification('success', title, message, duration);
    }
    
    /**
     * Hiển thị thông báo lỗi
     */
    error(title, message, duration) {
        return this.createNotification('error', title, message, duration);
    }
    
    /**
     * Hiển thị thông báo cảnh báo
     */
    warning(title, message, duration) {
        return this.createNotification('warning', title, message, duration);
    }
    
    /**
     * Hiển thị thông báo thông tin
     */
    info(title, message, duration) {
        return this.createNotification('info', title, message, duration);
    }
}

// Khởi tạo hệ thống thông báo
const notifySystem = new NotificationSystem();

/**
 * Xử lý mở rộng/thu gọn chi tiết sản phẩm
 * @param {HTMLElement} button - Button được click
 */
function toggleProduct(button) {
    const productCard = button.closest('.product-card');
    const details = productCard.querySelector('.product-details');
    const icon = button.querySelector('i');
    
    if (details.classList.contains('expanded')) {
        details.classList.remove('expanded');
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    } else {
        details.classList.add('expanded');
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    }
}

/**
 * Chuyển đổi chế độ chỉnh sửa cho thông số sản phẩm
 * @param {string} id - ID của thông số
 */
function toggleEdit(id) {
    const valueElement = document.getElementById('value-' + id);
    const editForm = document.getElementById('edit-' + id);
    
    if (editForm.style.display === 'none') {
        editForm.style.display = 'flex';
        valueElement.parentElement.style.display = 'none';
    } else {
        editForm.style.display = 'none';
        valueElement.parentElement.style.display = 'flex';
    }
}

/**
 * Hủy chỉnh sửa thông số
 * @param {string} id - ID của thông số
 */
function cancelEdit(id) {
    toggleEdit(id);
}

/**
 * Lưu thông số sau khi chỉnh sửa - Được gọi từ form chỉnh sửa thông thường
 * @param {string} id - ID của thông số
 */
function saveEdit(id) {
    const valueElement = document.getElementById('value-' + id);
    const editForm = document.getElementById('edit-' + id);
    const inputValue = editForm.querySelector('.edit-input').value;
    const statusValue = editForm.querySelector('.edit-select').value;
    
    // Cập nhật giá trị
    valueElement.textContent = inputValue;
    
    // Cập nhật trạng thái
    const statusElement = valueElement.nextElementSibling;
    statusElement.textContent = statusValue;
    
    // Cập nhật CSS cho trạng thái
    statusElement.className = 'spec-status';
    if (statusValue === 'Tốt') {
        statusElement.classList.add('status-good');
    } else if (statusValue === 'Cần kiểm tra' || statusValue === 'Trầy xước nhẹ') {
        statusElement.classList.add('status-check');
    } else {
        statusElement.classList.add('status-damaged');
    }
    
    // Đóng form chỉnh sửa
    toggleEdit(id);
    
    // Hiển thị thông báo
    notifySystem.success('Đã cập nhật', `Thông số "${valueElement.textContent}" đã được cập nhật.`);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Khởi tạo các biến DOM Elements
    searchInput = document.getElementById('searchInput');
    filterButtons = document.querySelectorAll('.filter-btn');
    filterMenus = document.querySelectorAll('.filter-menu');
    filterOptions = document.querySelectorAll('.filter-option');
    clearFiltersBtn = document.getElementById('clearFilters');
    productCards = document.querySelectorAll('.product-card');
    emptyState = document.getElementById('emptyState');
    productList = document.getElementById('productList');
    
    // Xử lý sự kiện cho nút bộ lọc nếu có
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                const menu = this.nextElementSibling;
                
                // Đóng tất cả menu khác
                filterMenus.forEach(otherMenu => {
                    if (otherMenu !== menu) {
                        otherMenu.classList.remove('show');
                    }
                });
                
                menu.classList.toggle('show');
            });
        });
        
        // Xử lý click bên ngoài để đóng dropdown
        document.addEventListener('click', function(event) {
            const isFilterBtn = event.target.closest('.filter-btn');
            const isFilterMenu = event.target.closest('.filter-menu');
            
            if (!isFilterBtn && !isFilterMenu) {
                filterMenus.forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        });
    }
    
    // Xử lý nút lưu thay đổi nếu có
    document.querySelectorAll('.btn-primary').forEach(btn => {
        if (btn.textContent.includes('Lưu thay đổi')) {
            btn.addEventListener('click', function() {
                const productCard = this.closest('.product-card');
                const productName = productCard.querySelector('.product-title').textContent;
                notifySystem.success('Đã lưu thay đổi', `Các thay đổi cho ${productName} đã được lưu thành công.`);
            });
        }
    });
    
    // Xử lý nút lịch sử nếu có
    document.querySelectorAll('.btn-secondary').forEach(btn => {
        if (btn.textContent.includes('Lịch sử')) {
            btn.addEventListener('click', function() {
                const productCard = this.closest('.product-card');
                const productName = productCard.querySelector('.product-title')?.textContent || 'Tài sản này';
                notifySystem.info('Lịch sử tài sản', `Đang tải lịch sử cho ${productName}...`);
            });
        }
    });
    
    // Xử lý nút QR code nếu có
    document.querySelectorAll('.btn-qrcode').forEach(btn => {
        btn.addEventListener('click', function() {
            const productCard = this.closest('.product-card');
            const productName = productCard.querySelector('.product-title')?.textContent || 'Tài sản này';
            notifySystem.info('Mã QR', `Đang tạo mã QR cho ${productName}...`);
        });
    });
    
    // Xử lý thêm tài sản mới nếu có
    const addAssetBtn = document.querySelector('.add-asset-btn');
    if (addAssetBtn) {
        addAssetBtn.addEventListener('click', function() {
            notifySystem.info('Thêm tài sản mới', 'Chức năng này sẽ được phát triển trong phiên bản tiếp theo.');
        });
    }
    
    // Hiển thị thông báo chào mừng sau 1s
    setTimeout(() => {
        notifySystem.success('Chào mừng', 'Chào mừng bạn đến với hệ thống quản lý tài sản!');
    }, 1000);
});