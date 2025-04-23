document.addEventListener('DOMContentLoaded', function() {
    // Lấy asset_id từ element data
    const assetElement = document.getElementById('asset-data');
    if (assetElement) {
        window.assetId = assetElement.getAttribute('data-asset-id');
        window.encodedId = assetElement.getAttribute('data-encoded-id');
    } else {
        // Fallback: lấy từ URL nếu không có element data
        const pathname = window.location.pathname;
        
        // Kiểm tra xem URL có phải định dạng mã hóa không (/a/...)
        if (pathname.startsWith('/a/')) {
            const encodedPart = pathname.replace('/a/', '');
            window.encodedId = encodedPart.split('?')[0]; // Loại bỏ query string nếu có
        } else {
            // URL thông thường (/assets/123)
            const matches = pathname.match(/\/assets\/(\d+)/);
            if (matches && matches.length > 1) {
                window.assetId = matches[1];
            }
        }
    }
    
    console.log("Asset ID:", window.assetId);
    console.log("Encoded ID:", window.encodedId);
});
// Kiểm tra xem một thông số có phải là giá trị tiền tệ không
function isCurrencySpec(specName) {
    specName = specName.toLowerCase();
    return specName.includes('giá') || 
           specName.includes('tiền') ||
           specName.includes('chi phí') ||
           specName.includes('phí') ||
           specName.includes('ngân sách') ||
           specName.includes('đồng');
}

// Hàm định dạng số thành tiền VNĐ
function formatCurrency(value) {
    // Loại bỏ các ký tự không phải số
    let numValue = value.toString().replace(/[^\d]/g, '');
    if (numValue === '') return '';
    
    // Định dạng số với dấu chấm ngăn cách hàng nghìn (kiểu Việt Nam)
    let formattedNumber = '';
    while (numValue.length > 3) {
        formattedNumber = '.' + numValue.substring(numValue.length - 3) + formattedNumber;
        numValue = numValue.substring(0, numValue.length - 3);
    }
    formattedNumber = numValue + formattedNumber;
    
    return `${formattedNumber} VNĐ`;
}

// Xử lý nhập liệu cho form chỉnh sửa
function handleEditInput(input, specName) {
    if (isCurrencySpec(specName)) {
        // Lưu vị trí con trỏ trước khi thay đổi giá trị
        const start = input.selectionStart;
        const end = input.selectionEnd;
        const originalLength = input.value.length;
        
        // Chỉ giữ lại các số
        let numValue = input.value.replace(/[^\d]/g, '');
        if (numValue) {
            // Định dạng số với dấu chấm ngăn cách hàng nghìn
            input.value = formatCurrency(numValue);
            
            // Điều chỉnh vị trí con trỏ sau khi định dạng
            const newLength = input.value.length;
            const diff = newLength - originalLength;
            input.setSelectionRange(start + diff, end + diff);
        }
    }
}

// Xử lý nhập liệu giá trị trên form thêm mới
function handleValueInput(input) {
    const specName = document.getElementById('spec-name');
    const specNameText = specName.options[specName.selectedIndex].text;
    const formatHint = document.getElementById('value-format-hint');
    
    // Nếu là thông số giá tiền
    if (isCurrencySpec(specNameText)) {
        formatHint.style.display = 'block';
        
        // Chỉ giữ lại các số
        let numValue = input.value.replace(/[^\d]/g, '');
        if (numValue) {
            // Định dạng số với dấu chấm ngăn cách hàng nghìn
            input.value = formatCurrency(numValue);
        }
    } else {
        formatHint.style.display = 'none';
    }
}

// Hiển thị/ẩn form chỉnh sửa
function toggleEdit(specId) {
    const card = document.querySelector(`.spec-card[data-spec-id="${specId}"]`);
    const valueDisplay = card.querySelector('.spec-value-display');
    const editForm = document.getElementById(`edit-${specId}`);
    
    if (editForm.style.display === 'none') {
        // Ẩn tất cả các form khác trước khi hiển thị form hiện tại
        document.querySelectorAll('.edit-form').forEach(form => {
            form.style.display = 'none';
            const id = form.id.replace('edit-', '');
            const otherCard = document.querySelector(`.spec-card[data-spec-id="${id}"]`);
            if (otherCard) {
                otherCard.querySelector('.spec-value-display').style.display = 'flex';
            }
        });
        
        // Hiển thị form hiện tại
        valueDisplay.style.display = 'none';
        editForm.style.display = 'flex';
        
        // Focus vào input
        const input = editForm.querySelector('.edit-input');
        input.focus();
        
        // Nếu là thông số tiền tệ, tạm thời hiển thị giá trị thuần túy để dễ chỉnh sửa
        const specName = editForm.dataset.specName;
        if (isCurrencySpec(specName)) {
            // Giữ lại dấu nháy cuối cùng
            input.selectionStart = input.value.length;
            input.selectionEnd = input.value.length;
        }
    } else {
        // Ẩn form
        valueDisplay.style.display = 'flex';
        editForm.style.display = 'none';
    }
}

// Hủy chỉnh sửa
function cancelEdit(specId) {
    const card = document.querySelector(`.spec-card[data-spec-id="${specId}"]`);
    const valueDisplay = card.querySelector('.spec-value-display');
    const editForm = document.getElementById(`edit-${specId}`);
    
    // Khôi phục giá trị gốc
    const originalValue = document.getElementById(`value-${specId}`).textContent.trim();
    editForm.querySelector('.edit-input').value = originalValue;
    
    // Ẩn form chỉnh sửa
    valueDisplay.style.display = 'flex';
    editForm.style.display = 'none';
}

// Chuyển đổi giữa các tab
function switchTab(tabName) {
    // Ẩn tất cả nội dung tab
    document.querySelectorAll('.spec-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Bỏ active tất cả các button tab
    document.querySelectorAll('.spec-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Hiển thị tab được chọn
    document.getElementById(`${tabName}-content`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// Hiển thị form thêm thông số
function showAddSpecForm() {
    document.getElementById('add-spec-modal').style.display = 'flex';
    
    // Kiểm tra thông số ngay khi mở form
    const specName = document.getElementById('spec-name');
    const specNameText = specName.options[specName.selectedIndex].text;
    const formatHint = document.getElementById('value-format-hint');
    
    if (isCurrencySpec(specNameText)) {
        formatHint.style.display = 'block';
    } else {
        formatHint.style.display = 'none';
    }
}

// Ẩn form thêm thông số
function hideAddSpecForm() {
    document.getElementById('add-spec-modal').style.display = 'none';
}

// Thêm thông số từ thông số chung vào thông số riêng
function addSpecFromGroup(assetId, thongsoId, thongsoName) {
    // Đặt giá trị cho form
    document.getElementById('spec-name').value = thongsoId;
    document.getElementById('spec-value').value = '';
    document.getElementById('spec-status').value = 'Tốt';
    
    // Hiển thị modal
    showAddSpecForm();
}

// Thêm thông số mới
function addNewSpec(assetId) {
    const thongsoSelect = document.getElementById('spec-name');
    const thongsoId = thongsoSelect.value;
    const thongsoName = thongsoSelect.options[thongsoSelect.selectedIndex].text;
    let value = document.getElementById('spec-value').value;
    const status = document.getElementById('spec-status').value;
    
    if (!thongsoId || !value) {
        notifySystem.warning('Thiếu thông tin', 'Vui lòng nhập đầy đủ thông tin thông số.');
        return;
    }
    
    // Lưu giá trị gốc để hiển thị thông báo
    const originalValue = value;
    
    // Nếu là giá trị tiền tệ, chỉ giữ lại số
    if (isCurrencySpec(thongsoName)) {
        value = value.replace(/[^\d]/g, '');
    }
    
    // Sử dụng ID tài sản từ biến toàn cục nếu không được truyền vào
    const actualAssetId = assetId || window.assetId;
    
    if (!actualAssetId) {
        notifySystem.error('Lỗi', 'Không thể xác định ID tài sản');
        return;
    }
    
    // Gửi API request để thêm thông số mới
    fetch(`/api/assets/${actualAssetId}/specifications/add`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            thongso_id: thongsoId,
            value: value,
            status: status
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Hiển thị thông báo thành công
            notifySystem.success('Đã thêm', 'Thông số mới đã được thêm thành công.');
            
            // Đóng modal
            hideAddSpecForm();
            
            // Làm mới trang sau 1 giây
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            // Hiển thị thông báo lỗi
            notifySystem.error('Lỗi', data.error || 'Không thể thêm thông số mới.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        notifySystem.error('Lỗi', 'Đã xảy ra lỗi khi thêm thông số mới.');
    });
}

function saveSpecEdit(specId) {
    const card = document.querySelector(`.spec-card[data-spec-id="${specId}"]`);
    const editForm = document.getElementById(`edit-${specId}`);
    const valueDisplay = card.querySelector('.spec-value-display');
    const specName = editForm.dataset.specName;
    let valueInput = editForm.querySelector('.edit-input').value;
    const statusSelect = editForm.querySelector('.edit-select').value;
    
    // Hiển thị loading hoặc disable button để tránh submit nhiều lần
    const saveBtn = editForm.querySelector('.save-btn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    // Lưu giá trị ban đầu để hiển thị lại nếu có lỗi
    const originalValue = valueInput;
    
    // Xử lý giá trị nếu là thông số tiền tệ
    if (isCurrencySpec(specName)) {
        // Chỉ giữ lại số khi gửi lên server
        valueInput = valueInput.replace(/[^\d]/g, '');
    }
    
    // Gửi API request để cập nhật
    fetch(`/api/specifications/${specId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            value: valueInput,
            status: statusSelect
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Cập nhật giao diện
            const valueDisplay = document.getElementById(`value-${specId}`);
            
            // Nếu là giá trị tiền tệ, định dạng lại
            if (isCurrencySpec(specName)) {
                valueDisplay.textContent = formatCurrency(valueInput);
            } else {
                valueDisplay.textContent = valueInput;
            }
            
            // Cập nhật status class
            const statusElement = valueDisplay.nextElementSibling;
            statusElement.textContent = statusSelect;
            statusElement.className = 'spec-status';
            
            if (statusSelect === 'Tốt') {
                statusElement.classList.add('status-good');
            } else if (statusSelect === 'Cần kiểm tra' || statusSelect === 'Trầy xước nhẹ') {
                statusElement.classList.add('status-check');
            } else {
                statusElement.classList.add('status-damaged');
            }
            
            // Đóng form edit
            toggleEdit(specId);
            
            // Hiển thị thông báo thành công
            notifySystem.success('Đã cập nhật', `Thông số đã được cập nhật.`);
            
            // Cập nhật thời gian cập nhật nếu có
            const footer = card.querySelector('.spec-card-footer');
            if (!footer) {
                // Tạo footer mới nếu chưa có
                const newFooter = document.createElement('div');
                newFooter.className = 'spec-card-footer';
                newFooter.innerHTML = `
                    <div class="spec-updated">
                        <i class="fas fa-clock"></i> ${new Date().toLocaleString('vi-VN')}
                    </div>
                `;
                card.appendChild(newFooter);
            } else {
                // Cập nhật thời gian trong footer hiện tại
                footer.querySelector('.spec-updated').innerHTML = `
                    <i class="fas fa-clock"></i> ${new Date().toLocaleString('vi-VN')}
                `;
            }
        } else {
            // Hiển thị thông báo lỗi
            notifySystem.error('Lỗi', data.error || 'Không thể cập nhật thông số.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        notifySystem.error('Lỗi', 'Đã xảy ra lỗi khi cập nhật thông số.');
    })
    .finally(() => {
        // Khôi phục trạng thái ban đầu của nút
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-check"></i>';
    });
}

// Hàm mở rộng/thu gọn phần thông số kỹ thuật
function toggleProduct(btn) {
    const productCard = btn.closest('.product-card');
    const productDetails = productCard.querySelector('.product-details');
    const icon = btn.querySelector('i');
    
    if (productDetails.classList.contains('expanded')) {
        productDetails.classList.remove('expanded');
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    } else {
        productDetails.classList.add('expanded');
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    }
}

// Thêm event listener khi trang đã tải xong
document.addEventListener('DOMContentLoaded', function() {
    const specNameSelect = document.getElementById('spec-name');
    if (specNameSelect) {
        specNameSelect.addEventListener('change', function() {
            const specNameText = this.options[this.selectedIndex].text;
            const specValue = document.getElementById('spec-value');
            const formatHint = document.getElementById('value-format-hint');
            
            if (isCurrencySpec(specNameText)) {
                formatHint.style.display = 'block';
                // Nếu đã có giá trị, định dạng lại
                if (specValue.value) {
                    specValue.value = formatCurrency(specValue.value.replace(/[^\d]/g, ''));
                }
            } else {
                formatHint.style.display = 'none';
            }
        });
    }
});
// Function to perform specification search
function searchSpecifications() {
    const searchInput = document.getElementById('spec-search-input');
    const searchTerm = searchInput.value.toLowerCase().trim();
    const searchResultsCount = document.getElementById('search-results-count');
    
    // Get all spec cards in both tabs
    const specificSpecCards = document.querySelectorAll('#specific-content .spec-card');
    const groupSpecCards = document.querySelectorAll('#group-content .spec-card');
    const allSpecCards = [...specificSpecCards, ...groupSpecCards];
    
    let visibleCardCount = 0;
    
    // Search through all spec cards
    allSpecCards.forEach(card => {
        const specName = card.querySelector('.spec-name').textContent.toLowerCase();
        const specValue = card.querySelector('.spec-value-text') ? 
            card.querySelector('.spec-value-text').textContent.toLowerCase() : '';
        
        const isMatch = searchTerm === '' || 
            specName.includes(searchTerm) || 
            specValue.includes(searchTerm);
        
        if (isMatch) {
            card.classList.remove('hidden');
            card.classList.toggle('highlight', searchTerm !== '');
            visibleCardCount++;
        } else {
            card.classList.add('hidden');
            card.classList.remove('highlight');
        }
    });
    
    // Update search results count
    if (searchTerm) {
        searchResultsCount.textContent = `Tìm thấy ${visibleCardCount} kết quả`;
    } else {
        searchResultsCount.textContent = '';
    }
    
    // If no results found, show a message in both tabs
    const specificContent = document.getElementById('specific-content');
    const groupContent = document.getElementById('group-content');
    
    let noResultsElement = document.getElementById('no-search-results');
    if (visibleCardCount === 0 && searchTerm) {
        if (!noResultsElement) {
            noResultsElement = document.createElement('div');
            noResultsElement.id = 'no-search-results';
            noResultsElement.className = 'empty-spec';
            noResultsElement.innerHTML = `
                <div class="empty-spec-icon">
                    <i class="fas fa-search"></i>
                </div>
                <p>Không tìm thấy kết quả cho "${searchTerm}"</p>
            `;
            
            // Determine which tab to add the message to
            if (document.getElementById('tab-specific').classList.contains('active')) {
                specificContent.appendChild(noResultsElement);
            } else {
                groupContent.appendChild(noResultsElement);
            }
        }
    } else if (noResultsElement) {
        noResultsElement.remove();
    }
}

// Add event listener for search input
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('spec-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', searchSpecifications);
    }
});
// Cập nhật hàm chuyển đổi giữa các tab
function switchTab(tabName) {
    // Ẩn tất cả nội dung tab
    document.querySelectorAll('.spec-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Bỏ active tất cả các button tab
    document.querySelectorAll('.spec-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Hiển thị tab được chọn
    document.getElementById(`${tabName}-content`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// Hiển thị/ẩn form chỉnh sửa trong bảng
function toggleEdit(specId) {
    const editRow = document.getElementById(`edit-row-${specId}`);
    const isVisible = editRow.style.display === 'table-row';
    
    // Ẩn tất cả các hàng chỉnh sửa đang mở
    document.querySelectorAll('.edit-row').forEach(row => {
        row.style.display = 'none';
    });
    
    // Nếu chưa hiển thị, mở form edit
    if (!isVisible) {
        editRow.style.display = 'table-row';
        
        // Focus vào input
        const input = document.querySelector(`#edit-${specId} .edit-input`);
        if (input) {
            setTimeout(() => {
                input.focus();
                // Đặt con trỏ ở cuối
                input.selectionStart = input.value.length;
                input.selectionEnd = input.value.length;
            }, 50);
        }
    }
}

// Hủy chỉnh sửa
function cancelEdit(specId) {
    const editRow = document.getElementById(`edit-row-${specId}`);
    if (editRow) {
        // Ẩn hàng chỉnh sửa
        editRow.style.display = 'none';
        
        // Khôi phục giá trị gốc cho input
        const originalValue = document.getElementById(`value-${specId}`).textContent.trim();
        document.querySelector(`#edit-${specId} .edit-input`).value = originalValue;
    }
}

// Lưu thông tin chỉnh sửa
function saveSpecEdit(specId) {
    const editForm = document.getElementById(`edit-${specId}`);
    const valueInput = editForm.querySelector('.edit-input').value;
    const statusSelect = editForm.querySelector('.edit-select').value;
    const specName = editForm.dataset.specName;
    
    // Hiển thị loading trên nút lưu
    const saveBtn = editForm.querySelector('.save-btn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    // Lưu giá trị ban đầu để hiển thị lại nếu có lỗi
    const originalValue = valueInput;
    
    // Xử lý giá trị nếu là thông số tiền tệ
    let valueToSend = valueInput;
    if (isCurrencySpec(specName)) {
        // Chỉ giữ lại số khi gửi lên server
        valueToSend = valueInput.replace(/[^\d]/g, '');
    }
    
    // Gửi API request để cập nhật
    fetch(`/api/specifications/${specId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            value: valueToSend,
            status: statusSelect
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Cập nhật giá trị hiển thị trên bảng
            const valueDisplay = document.getElementById(`value-${specId}`);
            
            // Nếu là giá trị tiền tệ, định dạng lại
            if (isCurrencySpec(specName)) {
                valueDisplay.textContent = formatCurrency(valueToSend);
            } else {
                valueDisplay.textContent = valueInput;
            }
            
            // Tìm và cập nhật status trong hàng
            const row = document.querySelector(`.spec-row[data-spec-id="${specId}"]`);
            const statusElement = row.querySelector('.spec-status');
            statusElement.textContent = '';
            
            // Cập nhật icon cho status
            let iconClass = 'check-circle';
            if (statusSelect === 'Cần kiểm tra') iconClass = 'exclamation-circle';
            else if (statusSelect === 'Hư hỏng') iconClass = 'times-circle';
            
            // Thêm icon và text cho status
            const icon = document.createElement('i');
            icon.className = `fas fa-${iconClass}`;
            statusElement.appendChild(icon);
            statusElement.appendChild(document.createTextNode(' ' + statusSelect));
            
            // Cập nhật class cho status
            statusElement.className = 'spec-status';
            if (statusSelect === 'Tốt') {
                statusElement.classList.add('status-good');
            } else if (statusSelect === 'Cần kiểm tra' || statusSelect === 'Trầy xước nhẹ') {
                statusElement.classList.add('status-check');
            } else {
                statusElement.classList.add('status-damaged');
            }
            
            // Cập nhật thời gian
            const updatedCell = row.querySelector('.spec-updated-cell .spec-updated');
            updatedCell.innerHTML = `<i class="fas fa-clock"></i> ${new Date().toLocaleString('vi-VN')}`;
            
            // Ẩn form edit
            cancelEdit(specId);
            
            // Hiển thị thông báo thành công
            notifySystem.success('Đã cập nhật', `Thông số đã được cập nhật thành công.`);
        } else {
            // Hiển thị thông báo lỗi
            notifySystem.error('Lỗi', data.error || 'Không thể cập nhật thông số.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        notifySystem.error('Lỗi', 'Đã xảy ra lỗi khi cập nhật thông số.');
    })
    .finally(() => {
        // Khôi phục trạng thái ban đầu của nút
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-check"></i>';
    });
}

// Function to perform specification search (updated for table view)
function searchSpecifications() {
    const searchInput = document.getElementById('spec-search-input');
    const searchTerm = searchInput.value.toLowerCase().trim();
    const searchResultsCount = document.getElementById('search-results-count');
    
    // Get all table rows in the active tab
    let specRows = [];
    
    if (document.getElementById('specific-content').classList.contains('active')) {
        specRows = document.querySelectorAll('#specific-content .spec-row');
    } else {
        specRows = document.querySelectorAll('#group-content .spec-card');
    }
    
    let visibleRowCount = 0;
    
    // Search through all rows
    specRows.forEach(row => {
        const specName = row.querySelector('.spec-name').textContent.toLowerCase();
        const specValue = row.querySelector('.spec-value-text') ? 
            row.querySelector('.spec-value-text').textContent.toLowerCase() : '';
        
        const isMatch = searchTerm === '' || 
            specName.includes(searchTerm) || 
            specValue.includes(searchTerm);
        
        if (isMatch) {
            row.classList.remove('hidden');
            row.classList.toggle('highlight', searchTerm !== '');
            
            // Hide edit row if visible
            if (row.classList.contains('spec-row')) {
                const specId = row.dataset.specId;
                const editRow = document.getElementById(`edit-row-${specId}`);
                if (editRow) editRow.classList.remove('hidden');
            }
            
            visibleRowCount++;
        } else {
            row.classList.add('hidden');
            row.classList.remove('highlight');
            
            // Hide edit row
            if (row.classList.contains('spec-row')) {
                const specId = row.dataset.specId;
                const editRow = document.getElementById(`edit-row-${specId}`);
                if (editRow) editRow.classList.add('hidden');
            }
        }
    });
    
    // Update search results count
    if (searchTerm) {
        searchResultsCount.textContent = `Tìm thấy ${visibleRowCount} kết quả`;
    } else {
        searchResultsCount.textContent = '';
    }
    
    // If no results found, show a message
    const specificContent = document.getElementById('specific-content');
    const groupContent = document.getElementById('group-content');
    
    let noResultsElement = document.getElementById('no-search-results');
    if (visibleRowCount === 0 && searchTerm) {
        if (!noResultsElement) {
            noResultsElement = document.createElement('div');
            noResultsElement.id = 'no-search-results';
            noResultsElement.className = 'empty-spec';
            noResultsElement.innerHTML = `
                <div class="empty-spec-icon">
                    <i class="fas fa-search"></i>
                </div>
                <p>Không tìm thấy kết quả cho "${searchTerm}"</p>
            `;
            
            // Determine which tab to add the message to
            if (document.getElementById('tab-specific').classList.contains('active')) {
                specificContent.querySelector('.details-content').appendChild(noResultsElement);
            } else {
                groupContent.querySelector('.details-content').appendChild(noResultsElement);
            }
        }
    } else if (noResultsElement) {
        noResultsElement.remove();
    }
}

// Add responsive data-labels for mobile view
document.addEventListener('DOMContentLoaded', function() {
    // Thêm data-label cho các ô td trong bảng khi ở chế độ mobile
    const specTable = document.querySelector('.specs-table');
    if (specTable) {
        const headers = specTable.querySelectorAll('thead th');
        const rows = specTable.querySelectorAll('tbody tr.spec-row');
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            cells.forEach((cell, index) => {
                if (index < headers.length) {
                    cell.setAttribute('data-label', headers[index].textContent);
                }
            });
        });
    }
    
    // Gắn sự kiện cho input tìm kiếm
    const searchInput = document.getElementById('spec-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', searchSpecifications);
    }
});