    /**
     * Xử lý cập nhật thông tin tài sản
     */
    
    // Khởi tạo thông báo
    const notification = window.notifySystem || new NotificationSystem();
    
    // Hiển thị form chỉnh sửa thông tin tài sản
    function showEditAssetForm() {
        // Lấy thông tin tài sản hiện tại
        const assetElement = document.getElementById('asset-data');
        if (!assetElement) {
            notification.error('Lỗi', 'Không thể lấy thông tin tài sản');
            return;
        }
        
        const assetId = assetElement.getAttribute('data-asset-id');
        const encodedId = assetElement.getAttribute('data-encoded-id');
        
        // Đặt giá trị ID cho form
        document.getElementById('asset-id').value = assetId;
        
        // Lấy các giá trị hiện tại
        const statusEl = document.querySelector('.product-status');
        const statusText = statusEl ? statusEl.textContent.trim() : '';
        
        // Lấy giá trị số seri
        const seriValue = document.querySelector('.asset-detail-item:nth-of-type(3) .detail-value').textContent.trim();
        
        // Ngày sử dụng - chuyển đổi từ định dạng dd/mm/yyyy sang yyyy-mm-dd cho input date
        const useDateEl = document.querySelector('.asset-detail-item:nth-of-type(9) .detail-value');
        let useDate = '';
        if (useDateEl) {
            const dateText = useDateEl.textContent.trim();
            if (dateText && dateText !== 'Chưa có') {
                const parts = dateText.split('/');
                if (parts.length === 3) {
                    useDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
                }
            }
        }
        
        // Hạn bảo hành - chuyển đổi từ định dạng dd/mm/yyyy sang yyyy-mm-dd cho input date
        const warrantyEl = document.querySelector('.asset-detail-item:nth-of-type(11) .detail-value');
        let warranty = '';
        if (warrantyEl) {
            const warrantyText = warrantyEl.textContent.trim().split(' ')[0]; // Lấy phần ngày trước "Còn BH"/"Hết BH"
            if (warrantyText && warrantyText !== 'Chưa có') {
                const parts = warrantyText.split('/');
                if (parts.length === 3) {
                    warranty = `${parts[2]}-${parts[1]}-${parts[0]}`;
                }
            }
        }
        
        // Ghi chú
        const noteEl = document.querySelector('.asset-detail-item.grid-full:last-child .detail-value');
        const note = noteEl ? noteEl.textContent.trim() : '';
        
        // Đặt giá trị cho các trường trong form
        document.getElementById('asset-status').value = statusText;
        document.getElementById('asset-seri').value = seriValue.replace('Chưa có', '');
        document.getElementById('asset-date').value = useDate;
        document.getElementById('asset-warranty').value = warranty;
        document.getElementById('asset-note').value = note;
        
        // Hiển thị modal
        document.getElementById('edit-asset-modal').style.display = 'flex';
    }
    
    // Ẩn form chỉnh sửa thông tin tài sản
    function hideEditAssetForm() {
        document.getElementById('edit-asset-modal').style.display = 'none';
        
        // Reset thông báo lỗi
        document.getElementById('seri-error').style.display = 'none';
    }
    
    // Kiểm tra số seri có trùng lặp không
    async function checkSeriDuplicate(seri, assetId) {
        try {
            const response = await fetch(`/api/assets/check-seri?seri=${encodeURIComponent(seri)}&asset_id=${assetId}`);
            const data = await response.json();
            return data.duplicate;
        } catch (error) {
            console.error('Error checking seri:', error);
            return false; // Mặc định cho phép nếu không kiểm tra được
        }
    }
    
    // Lưu thông tin tài sản
    async function saveAssetInfo() {
        const assetId = document.getElementById('asset-id').value;
        const status = document.getElementById('asset-status').value;
        const seri = document.getElementById('asset-seri').value;
        const useDate = document.getElementById('asset-date').value;
        const warranty = document.getElementById('asset-warranty').value;
        const note = document.getElementById('asset-note').value;
        
        // Kiểm tra dữ liệu
        if (!status) {
            notification.warning('Thiếu thông tin', 'Vui lòng chọn tình trạng tài sản');
            return;
        }
        
        // Hiển thị loading
        const saveBtn = document.getElementById('save-asset-btn');
        const originalBtnHtml = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';
        
        // Kiểm tra số seri có trùng lặp không (nếu có nhập số seri)
        if (seri) {
            const isDuplicate = await checkSeriDuplicate(seri, assetId);
            if (isDuplicate) {
                document.getElementById('seri-error').style.display = 'block';
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalBtnHtml;
                return;
            } else {
                document.getElementById('seri-error').style.display = 'none';
            }
        }
        
        // Chuẩn bị dữ liệu gửi đi
        const data = {
            tinh_trang_sp: status,
            so_seri: seri,
            ghi_chu: note
        };
        
        // Thêm ngày sử dụng nếu có
        if (useDate) {
            data.ngay_su_dung = useDate;
        }
        
        // Thêm hạn bảo hành nếu có
        if (warranty) {
            data.han_bh = warranty;
        }
        
        // Gửi API request
        try {
            const response = await fetch(`/api/assets/${assetId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Hiển thị thông báo thành công
                notification.success('Thành công', 'Thông tin tài sản đã được cập nhật');
                
                // Đóng modal
                hideEditAssetForm();
                
                // Làm mới trang sau 1 giây
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                // Hiển thị thông báo lỗi
                notification.error('Lỗi', result.error || 'Không thể cập nhật thông tin tài sản');
            }
        } catch (error) {
            console.error('Error:', error);
            notification.error('Lỗi', 'Đã xảy ra lỗi khi cập nhật thông tin tài sản');
        } finally {
            // Khôi phục trạng thái nút
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalBtnHtml;
        }
    }
    
    // Thêm event listener khi DOM đã load xong
    document.addEventListener('DOMContentLoaded', function() {
        // Gắn sự kiện cho nút chỉnh sửa
        const editBtn = document.querySelector('.asset-actions .btn-primary');
        if (editBtn) {
            editBtn.addEventListener('click', showEditAssetForm);
        }
        
        // Gắn sự kiện cho nút lưu trong form chỉnh sửa
        const saveBtn = document.getElementById('save-asset-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', saveAssetInfo);
        }
        
        // Gắn sự kiện cho input số seri để xóa thông báo lỗi khi thay đổi
        const seriInput = document.getElementById('asset-seri');
        if (seriInput) {
            seriInput.addEventListener('input', function() {
                document.getElementById('seri-error').style.display = 'none';
            });
        }
    });