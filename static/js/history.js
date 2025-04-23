/**
 * Xử lý hiển thị lịch sử tài sản
 */

// Khởi tạo biến toàn cục
let assetHistory = [];
let currentFilter = 'all';

// Hiển thị modal lịch sử
function showHistoryModal() {
    // Lấy ID tài sản
    const assetId = window.assetId;
    if (!assetId) {
        notifySystem.error('Lỗi', 'Không thể xác định ID tài sản');
        return;
    }
    
    // Hiển thị modal
    document.getElementById('history-modal').style.display = 'flex';
    
    // Hiển thị trạng thái đang tải
    document.querySelector('.history-list').innerHTML = `
        <div class="history-loading">
            <i class="fas fa-spinner"></i> Đang tải lịch sử...
        </div>
    `;
    
    // Reset filter
    currentFilter = 'all';
    document.querySelectorAll('.history-filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === 'all');
    });
    
    // Gọi API lấy lịch sử
    fetchAssetHistory(assetId);
}

// Ẩn modal lịch sử
function hideHistoryModal() {
    document.getElementById('history-modal').style.display = 'none';
}

// Gọi API lấy lịch sử tài sản
function fetchAssetHistory(assetId) {
    fetch(`/api/assets/${assetId}/history`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Lưu lịch sử vào biến toàn cục
                assetHistory = data.history;
                
                // Hiển thị lịch sử
                renderAssetHistory();
            } else {
                // Hiển thị thông báo lỗi
                document.querySelector('.history-list').innerHTML = `
                    <div class="history-empty">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>${data.error || 'Không thể tải lịch sử tài sản'}</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.querySelector('.history-list').innerHTML = `
                <div class="history-empty">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Đã xảy ra lỗi khi tải lịch sử tài sản</p>
                </div>
            `;
        });
}

// Hiển thị lịch sử tài sản
function renderAssetHistory() {
    const historyListElement = document.querySelector('.history-list');
    
    // Lọc lịch sử theo bộ lọc hiện tại
    let filteredHistory = assetHistory;
    if (currentFilter !== 'all') {
        filteredHistory = assetHistory.filter(item => item.category === currentFilter);
    }
    
    // Kiểm tra nếu không có lịch sử
    if (!filteredHistory || filteredHistory.length === 0) {
        historyListElement.innerHTML = `
            <div class="history-empty">
                <i class="fas fa-history"></i>
                <p>Không có lịch sử nào được tìm thấy</p>
            </div>
        `;
        return;
    }
    
    // Tạo HTML cho từng mục lịch sử
    const historyItems = filteredHistory.map(item => {
        // Xác định icon dựa vào loại thông báo
        let iconClass = 'info-circle';
        switch(item.type) {
            case 'update':
                iconClass = 'pen';
                break;
            case 'warning':
                iconClass = 'exclamation-triangle';
                break;
            case 'error':
                iconClass = 'times-circle';
                break;
            case 'info':
            default:
                iconClass = 'info-circle';
                break;
        }
        
        // Nếu là bàn giao, dùng icon khác
        if (item.category === 'handover') {
            iconClass = 'exchange-alt';
        }
        
        // Tạo nội dung cho danh mục
        let categoryContent = '';
        switch(item.category) {
            case 'specification':
                categoryContent = '<i class="fas fa-cogs"></i> Thông số';
                break;
            case 'handover':
                categoryContent = '<i class="fas fa-exchange-alt"></i> Bàn giao';
                break;
            case 'general':
            default:
                categoryContent = '<i class="fas fa-info-circle"></i> Thông tin';
                break;
        }
        
        // Tạo link xem chi tiết nếu có
        let linkContent = '';
        if (item.link) {
            linkContent = `
                <a href="${item.link}" class="history-link">
                    <i class="fas fa-external-link-alt"></i> Xem chi tiết
                </a>
            `;
        }
        
        // Tạo HTML cho mục lịch sử
        return `
            <div class="history-item">
                <div class="history-icon ${item.type}">
                    <i class="fas fa-${iconClass}"></i>
                </div>
                <div class="history-content">
                    <div class="history-message">${item.message}</div>
                    <div class="history-meta">
                        <div class="history-time">
                            <i class="fas fa-clock"></i> ${item.created_at}
                        </div>
                        <div class="history-category">
                            ${categoryContent}
                        </div>
                        ${linkContent}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Hiển thị lịch sử
    historyListElement.innerHTML = historyItems;
}

// Thiết lập bộ lọc
function setHistoryFilter(filter) {
    currentFilter = filter;
    
    // Cập nhật trạng thái active của các nút
    document.querySelectorAll('.history-filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === filter);
    });
    
    // Cập nhật lại danh sách lịch sử
    renderAssetHistory();
}

// Thêm event listener khi DOM đã tải xong
document.addEventListener('DOMContentLoaded', function() {
    // Gắn sự kiện cho nút lịch sử
    document.querySelectorAll('.btn-secondary').forEach(btn => {
        if (btn.textContent.includes('Lịch sử')) {
            btn.addEventListener('click', showHistoryModal);
        }
    });
    
    // Gắn sự kiện cho nút lọc lịch sử
    document.querySelectorAll('.history-filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            setHistoryFilter(this.dataset.filter);
        });
    });
});