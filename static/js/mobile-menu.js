/**
 * Mobile Menu Handler
 * Xử lý menu mobile responsive với hiệu ứng đẹp mắt
 */
document.addEventListener('DOMContentLoaded', function() {
    // Kiểm tra kích thước màn hình để chỉ thực hiện trên mobile
    const isMobile = window.innerWidth <= 768;
    
    // Tạo nút hamburger menu và chèn vào header chỉ khi ở chế độ mobile
    const headerContainer = document.querySelector('.header-container');
    if (isMobile && headerContainer) {
        // Tạo hamburger menu nếu chưa tồn tại
        if (!document.querySelector('.hamburger-menu')) {
            const hamburgerMenu = document.createElement('div');
            hamburgerMenu.className = 'hamburger-menu';
            hamburgerMenu.innerHTML = '<i class="fas fa-bars"></i>';
            headerContainer.prepend(hamburgerMenu);
        }
        
        // Thêm overlay nếu chưa tồn tại
        if (!document.querySelector('.mobile-menu-overlay')) {
            const overlay = document.createElement('div');
            overlay.className = 'mobile-menu-overlay';
            document.body.appendChild(overlay);
        }
    }
    
    // Lấy hamburger menu và overlay (có thể đã tạo hoặc đã có sẵn)
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const overlay = document.querySelector('.mobile-menu-overlay');
    
    // Chỉ tiếp tục nếu các phần tử cần thiết tồn tại
    if (hamburgerMenu && overlay) {
        const mainNav = document.querySelector('.main-nav');
        
        // Nếu không có phần tử .user-profile, không thực hiện các thao tác với nó
        const userProfileElement = document.querySelector('.user-profile');
        let userAvatar = '';
        let userName = '';
        
        if (userProfileElement) {
            const avatarElement = userProfileElement.querySelector('img');
            const nameElement = userProfileElement.querySelector('span');
            
            userAvatar = avatarElement ? avatarElement.getAttribute('src') : 'https://via.placeholder.com/40';
            userName = nameElement ? nameElement.textContent : 'Admin';
        }
        
        // Thêm header cho nav nếu chưa có
        if (mainNav && !mainNav.querySelector('.nav-header')) {
            const navHeader = document.createElement('div');
            navHeader.className = 'nav-header';
            navHeader.innerHTML = `
                <div class="nav-logo">
                    <img src="{{ url_for('static', filename='img/logo/logo_dnc_single.png') }}" alt="logo" class="logo-img">
                </div>
                <div class="nav-close"><i class="fas fa-times"></i></div>
            `;
            mainNav.prepend(navHeader);
            
            // Thêm thông tin người dùng nếu có đủ dữ liệu
            const navUser = document.createElement('div');
            navUser.className = 'nav-user';
            navUser.innerHTML = `
                <img src="${userAvatar}" alt="User Avatar">
                <div class="nav-user-info">
                    <div class="nav-user-name">${userName}</div>
                    <div class="nav-user-role">Quản trị viên</div>
                </div>
            `;
            mainNav.insertBefore(navUser, mainNav.querySelector('ul'));
            
            // Thêm footer cho navigation
            const navFooter = document.createElement('div');
            navFooter.className = 'nav-footer';
            navFooter.innerHTML = `
                <p>&copy; 2025 AssetManager - Phiên bản 1.0.2</p>
            `;
            mainNav.appendChild(navFooter);
        }
        
        // Làm đẹp cấu trúc menu items
        const menuItems = mainNav.querySelectorAll('li a');
        menuItems.forEach(item => {
            // Không thay đổi cấu trúc nếu đã được xử lý (có chứa span.menu-text)
            if (!item.querySelector('.menu-text')) {
                // Giữ nội dung gốc
                const iconElement = item.querySelector('i');
                
                if (iconElement) {
                    const clonedIcon = iconElement.cloneNode(true);
                    
                    // Lưu lại nội dung text
                    let textContent = item.textContent.trim();
                    if (iconElement.textContent) {
                        textContent = textContent.replace(iconElement.textContent, '').trim();
                    }
                    
                    // Xóa nội dung hiện tại
                    item.innerHTML = '';
                    
                    // Thêm lại icon
                    item.appendChild(clonedIcon);
                    
                    // Thêm text node bọc trong span
                    const textSpan = document.createElement('span');
                    textSpan.className = 'menu-text';
                    textSpan.textContent = textContent;
                    item.appendChild(textSpan);
                }
            }
        });
        
        // Thêm badge "Mới" vào menu item thứ 3 (Thêm tài sản) nếu chưa có
        if (menuItems.length >= 3 && !menuItems[2].querySelector('.badge')) {
            const badgeEl = document.createElement('span');
            badgeEl.className = 'badge';
            badgeEl.textContent = 'Mới';
            menuItems[2].appendChild(badgeEl);
        }
        
        // Xử lý sự kiện mở menu
        hamburgerMenu.addEventListener('click', function() {
            mainNav.classList.add('active');
            overlay.style.display = 'block';
            setTimeout(() => {
                overlay.classList.add('active');
            }, 10);
            document.body.style.overflow = 'hidden'; // Ngăn scroll
        });
        
        // Xử lý sự kiện đóng menu
        const closeNav = function() {
            mainNav.classList.remove('active');
            overlay.classList.remove('active');
            
            // Đợi animation hoàn thành rồi mới ẩn overlay
            setTimeout(() => {
                overlay.style.display = 'none';
                document.body.style.overflow = ''; // Cho phép scroll lại
            }, 300);
        };
        
        const navCloseBtn = mainNav.querySelector('.nav-close');
        if (navCloseBtn) {
            navCloseBtn.addEventListener('click', closeNav);
        }
        
        overlay.addEventListener('click', closeNav);
        
        // Đóng menu khi click vào một mục trong menu
        mainNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeNav);
        });
        
        // Xử lý hiệu ứng ripple khi click vào menu items
        mainNav.querySelectorAll('li a').forEach(link => {
            link.addEventListener('click', function(e) {
                // Kiểm tra xem đã có ripple effect chưa
                if (!this.querySelector('.ripple')) {
                    const rect = this.getBoundingClientRect();
                    const ripple = document.createElement('span');
                    
                    ripple.className = 'ripple';
                    ripple.style.cssText = `
                        position: absolute;
                        background-color: rgba(255, 255, 255, 0.7);
                        border-radius: 50%;
                        width: 5px;
                        height: 5px;
                        animation: ripple 0.6s linear;
                        left: ${e.clientX - rect.left}px;
                        top: ${e.clientY - rect.top}px;
                    `;
                    
                    this.appendChild(ripple);
                    
                    setTimeout(() => {
                        ripple.remove();
                    }, 600);
                }
            });
        });
    }
    
    // Thêm animation keyframes cho ripple effect nếu chưa có
    if (!document.getElementById('ripple-style')) {
        const style = document.createElement('style');
        style.id = 'ripple-style';
        style.textContent = `
            @keyframes ripple {
                0% {
                    transform: scale(0);
                    opacity: 0.5;
                }
                100% {
                    transform: scale(100);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Thêm sự kiện lắng nghe thay đổi kích thước màn hình
    window.addEventListener('resize', function() {
        const newIsMobile = window.innerWidth <= 768;
        
        // Nếu chuyển từ desktop sang mobile
        if (!isMobile && newIsMobile) {
            // Tải lại trang để áp dụng styles mới
            location.reload();
        } 
        // Nếu chuyển từ mobile sang desktop
        else if (isMobile && !newIsMobile) {
            const mainNav = document.querySelector('.main-nav');
            if (mainNav) {
                mainNav.classList.remove('active');
            }
            
            const overlay = document.querySelector('.mobile-menu-overlay');
            if (overlay) {
                overlay.style.display = 'none';
                overlay.classList.remove('active');
            }
            
            document.body.style.overflow = '';
            
            // Tải lại trang để áp dụng styles mới
            location.reload();
        }
    });
});