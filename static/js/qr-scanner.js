/**
 * QR Scanner với tính năng phản hồi tương thích cho cả Desktop và Mobile
 * Cải tiến tính năng và xử lý thiết bị đa dạng
 */
document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('qr-video');
    const switchCameraButton = document.getElementById('switchCamera');
    const toggleFlashButton = document.getElementById('toggleFlash');
    const retryButton = document.getElementById('retryCamera');
    const cameraStatus = document.getElementById('cameraStatus');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorContainer = document.getElementById('error-container');
    const errorText = document.getElementById('error-text');
    const browserInfo = document.getElementById('browser-info');
    const scannerContainer = document.querySelector('.scanner-container');
    const scannerFrame = document.querySelector('.scanner-frame');
    
    let currentStream = null;
    let facingMode = 'environment'; // Mặc định sử dụng camera sau
    let flashlight = null;
    let scannerActive = false;
    let lastDetectionTime = 0; // Phòng tránh quét trùng lặp
    let isDesktop = window.innerWidth >= 768;
    
    // Hiển thị thông tin trình duyệt để debug
    function getBrowserInfo() {
        const ua = navigator.userAgent;
        let browserName = "Unknown";
        let browserVersion = "";
        let deviceInfo = "";
        
        // Detect device type
        if (/Android/i.test(ua)) {
            deviceInfo = "Android";
        } else if (/iPhone|iPad|iPod/i.test(ua)) {
            deviceInfo = "iOS";
        } else if (/Windows Phone/i.test(ua)) {
            deviceInfo = "Windows Phone";
        } else if (/Windows/i.test(ua)) {
            deviceInfo = "Windows";
        } else if (/Macintosh/i.test(ua)) {
            deviceInfo = "Mac";
        } else if (/Linux/i.test(ua)) {
            deviceInfo = "Linux";
        }
        
        // Detect browser
        if (ua.indexOf("Firefox") > -1) {
            browserName = "Firefox";
            browserVersion = ua.match(/Firefox\/([\d.]+)/)[1];
        } else if (ua.indexOf("SamsungBrowser") > -1) {
            browserName = "Samsung Internet";
            browserVersion = ua.match(/SamsungBrowser\/([\d.]+)/)[1];
        } else if (ua.indexOf("Opera") > -1 || ua.indexOf("OPR") > -1) {
            browserName = "Opera";
            browserVersion = ua.indexOf("Opera") > -1 ? 
                ua.match(/Opera\/([\d.]+)/)[1] : 
                ua.match(/OPR\/([\d.]+)/)[1];
        } else if (ua.indexOf("Edg") > -1) {
            browserName = "Microsoft Edge";
            browserVersion = ua.match(/Edg\/([\d.]+)/)[1];
        } else if (ua.indexOf("Chrome") > -1) {
            browserName = "Chrome";
            browserVersion = ua.match(/Chrome\/([\d.]+)/)[1];
        } else if (ua.indexOf("Safari") > -1) {
            browserName = "Safari";
            browserVersion = ua.match(/Version\/([\d.]+)/)[1];
        }
        
        return `${deviceInfo} - ${browserName} ${browserVersion}`;
    }
    
    browserInfo.textContent = `Thiết bị: ${getBrowserInfo()}, Giao thức: ${window.location.protocol}`;
    
    // Kiểm tra giao thức HTTP
    if (window.location.protocol === 'http:' && 
        window.location.hostname !== 'localhost' && 
        !window.location.hostname.startsWith('192.168.') && 
        !window.location.hostname.startsWith('127.0.0.1')) {
        showError('Để sử dụng camera, vui lòng truy cập qua HTTPS hoặc localhost. Hiện tại bạn đang sử dụng HTTP không bảo mật.');
    }
    
    // Kiểm tra hỗ trợ API camera
    function checkCameraSupport() {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            return true;
        }
        
        if (navigator.getUserMedia || 
            navigator.webkitGetUserMedia || 
            navigator.mozGetUserMedia || 
            navigator.msGetUserMedia) {
            // Polyfill cho các trình duyệt cũ
            navigator.mediaDevices = { getUserMedia: function(constraints) {
                const getUserMedia = navigator.getUserMedia || 
                                    navigator.webkitGetUserMedia || 
                                    navigator.mozGetUserMedia || 
                                    navigator.msGetUserMedia;
                
                return new Promise(function(resolve, reject) {
                    getUserMedia.call(navigator, constraints, resolve, reject);
                });
            }};
            return true;
        }
        
        return false;
    }
    
    // Hiển thị lỗi với nút thử lại và hiệu ứng
    function showError(message) {
        errorText.textContent = message;
        errorContainer.style.display = 'block';
        
        // Thay đổi màu của camera status
        cameraStatus.textContent = message;
        cameraStatus.style.color = '#d32f2f';
        cameraStatus.style.backgroundColor = '#ffebee';
        
        // Thêm hiệu ứng rung nhẹ
        errorContainer.classList.add('shake-animation');
        setTimeout(() => {
            errorContainer.classList.remove('shake-animation');
        }, 500);
    }
    
    // Hiệu ứng CSS cho thông báo lỗi và hiệu ứng quét
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .shake-animation {
            animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
        }
        @keyframes shake {
            10%, 90% { transform: translate3d(-1px, 0, 0); }
            20%, 80% { transform: translate3d(2px, 0, 0); }
            30%, 50%, 70% { transform: translate3d(-3px, 0, 0); }
            40%, 60% { transform: translate3d(3px, 0, 0); }
        }
        
        .success-scan {
            animation: success-pulse 0.5s;
        }
        @keyframes success-pulse {
            0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.5); }
            70% { box-shadow: 0 0 0 20px rgba(76, 175, 80, 0); }
            100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
        }
        
        .button-pressed {
            transform: scale(0.95);
            opacity: 0.9;
        }
        .btn-switch-camera, .btn-retry {
            transition: transform 0.2s, opacity 0.2s, background-color 0.3s;
        }
        .btn-switch-camera:active, .btn-retry:active {
            transform: scale(0.95);
            opacity: 0.9;
        }
        
        @media (min-width: 769px) {
            .desktop-only {
                display: flex;
            }
        }
        
        @media (max-width: 768px) {
            .desktop-only {
                display: none;
            }
        }
    `;
    document.head.appendChild(styleElement);
    
    // Kiểm tra hỗ trợ camera
    if (!checkCameraSupport()) {
        showError('Trình duyệt của bạn không hỗ trợ quét mã QR. Vui lòng sử dụng Chrome, Firefox, Edge, hoặc Safari phiên bản mới nhất.');
        return;
    }
    
    // Tối ưu kích thước video cho thiết bị
    function optimizeVideoConstraints() {
        if (isDesktop) {
            // Desktop hoặc tablet
            return {
                facingMode: facingMode,
                width: { ideal: 1280 },
                height: { ideal: 720 }
            };
        } else {
            // Mobile
            const isPortrait = window.innerHeight > window.innerWidth;
            
            if (isPortrait) {
                return {
                    facingMode: facingMode,
                    width: { ideal: 720 },
                    height: { ideal: 1280 }
                };
            } else {
                return {
                    facingMode: facingMode,
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                };
            }
        }
    }
    
    // Khởi tạo camera với xử lý lỗi chi tiết
    async function startCamera() {
        if (currentStream) {
            // Dừng stream hiện tại nếu có
            currentStream.getTracks().forEach(track => track.stop());
        }
        
        scannerActive = false;
        errorContainer.style.display = 'none';
        
        // Cập nhật UI
        cameraStatus.textContent = 'Đang khởi tạo camera...';
        cameraStatus.style.color = 'var(--text-color-secondary)';
        cameraStatus.style.backgroundColor = '#f8f9fa';
        loadingIndicator.style.display = 'flex';
        
        try {
            const constraints = {
                video: optimizeVideoConstraints(),
                audio: false
            };
            
            // Lấy stream từ camera
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            currentStream = stream;
            video.srcObject = stream;
            
            // Kiểm tra khả năng hỗ trợ flash
            const videoTrack = stream.getVideoTracks()[0];
            if (videoTrack.getCapabilities && videoTrack.getCapabilities().torch) {
                toggleFlashButton.style.display = 'inline-flex';
                flashlight = videoTrack;
            } else {
                toggleFlashButton.style.display = 'none';
                flashlight = null;
            }
            
            // Bắt đầu quét khi video đã sẵn sàng
            video.onloadedmetadata = function() {
                // Ẩn loading
                loadingIndicator.style.display = 'none';
                video.play();
                cameraStatus.textContent = 'Camera đã sẵn sàng, đang quét...';
                cameraStatus.style.color = '#4caf50';
                scannerActive = true;
                
                // Thêm class để hiển thị animation
                scannerContainer.classList.add('camera-ready');
                
                // Bắt đầu quét
                scanQRCode();
            };
        } catch (error) {
            console.error('Lỗi khi khởi tạo camera:', error);
            loadingIndicator.style.display = 'none';
            
            let errorMessage = 'Không thể khởi tạo camera';
            
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                errorMessage = 'Bạn đã từ chối quyền truy cập camera. Vui lòng cấp quyền và tải lại trang.';
            } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                errorMessage = 'Không tìm thấy camera nào trên thiết bị này.';
            } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                errorMessage = 'Camera đang được sử dụng bởi ứng dụng khác hoặc không thể truy cập.';
            } else if (error.name === 'OverconstrainedError') {
                errorMessage = 'Không tìm thấy camera phù hợp với yêu cầu.';
            } else if (error.name === 'AbortError') {
                errorMessage = 'Quá trình kết nối với camera đã bị hủy.';
            } else if (error.name === 'TypeError') {
                errorMessage = 'Trình duyệt không hỗ trợ định dạng yêu cầu camera.';
            }
            
            showError(`${errorMessage} (${error.name})`);
        }
    }
    
    // Quét QR từ video stream với tối ưu hiệu suất
    function scanQRCode() {
        if (!scannerActive) {
            return; // Dừng quét nếu scanner không còn hoạt động
        }
        
        if (!video.videoWidth) {
            // Nếu video chưa sẵn sàng, thử lại sau 100ms
            setTimeout(scanQRCode, 100);
            return;
        }
        
        // Tạo canvas để xử lý ảnh
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d', { willReadFrequently: true });
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Biến đếm frame để tối ưu hiệu suất
        let frameCount = 0;
        
        // Tần suất xử lý frame dựa vào thiết bị
        const frameSkip = isDesktop ? 2 : 3; // Desktop xử lý nhiều frame hơn
        
        // Hàm quét liên tục
        function scan() {
            if (!scannerActive) {
                return; // Dừng quét khi scanner không còn hoạt động
            }
            
            frameCount++;
            // Chỉ xử lý một số frame nhất định để giảm tải CPU
            if (frameCount % frameSkip !== 0) {
                requestAnimationFrame(scan);
                return;
            }
            
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                try {
                    // Vẽ frame hiện tại vào canvas
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                    
                    // Quét mã QR với các tùy chọn tối ưu hiệu suất
                    const code = jsQR(imageData.data, imageData.width, imageData.height, {
                        inversionAttempts: "dontInvert", // Tăng hiệu suất trên mobile
                    });
                    
                    if (code) {
                        // Xử lý khi tìm thấy mã QR
                        const currentTime = new Date().getTime();
                        if (currentTime - lastDetectionTime > 1500) { // Tránh quét trùng lặp trong 1.5s
                            lastDetectionTime = currentTime;
                            handleQRCode(code.data);
                            return; // Dừng quét sau khi tìm thấy QR hợp lệ
                        }
                    }
                } catch (error) {
                    console.error('Lỗi khi quét QR:', error);
                    // Không hiển thị lỗi cho người dùng nếu chỉ là lỗi xử lý frame
                }
            }
            
            // Lặp lại quét cho frame tiếp theo
            requestAnimationFrame(scan);
        }
        
        scan();
    }
    
    // Xử lý khi phát hiện mã QR
    function handleQRCode(qrData) {
        console.log('Đã phát hiện mã QR:', qrData);
        
        // Ngừng xử lý các mã QR mới
        scannerActive = false;
        
        // Hiệu ứng thành công khi quét được mã QR
        scannerFrame.classList.add('success-scan');
        
        // Kiểm tra xem qrData có phải là URL hợp lệ không
        if (!qrData.startsWith('http')) {
            // Hiển thị thông báo lỗi
            cameraStatus.textContent = `Mã không hợp lệ: ${qrData}`;
            cameraStatus.style.color = '#ff9800';
            
            // Cho phép quét tiếp sau 1.5 giây
            setTimeout(() => {
                scannerFrame.classList.remove('success-scan');
                scannerActive = true;
            }, 1500);
            return;
        }
        
        // Kiểm tra xem URL có chứa các tham số cần thiết không
        try {
            const url = new URL(qrData);
            
            // Nếu là URL hợp lệ và có các tham số id hoặc seri
            if (url.searchParams.has('id') || url.searchParams.has('seri')) {
                // Hiển thị loading và điều hướng đến URL
                loadingIndicator.style.display = 'flex';
                cameraStatus.textContent = 'Đã tìm thấy mã QR hợp lệ. Đang chuyển hướng...';
                cameraStatus.style.color = '#4caf50';
                
                // Dừng tất cả luồng camera
                if (currentStream) {
                    currentStream.getTracks().forEach(track => track.stop());
                }
                
                // Thêm tiếng beep nếu được hỗ trợ
                playSuccessSound();
                
                // Chuyển hướng đến URL trong mã QR (thêm timeout nhỏ để hiển thị loading)
                setTimeout(() => {
                    window.location.href = qrData;
                }, 800);
            } else {
                cameraStatus.textContent = 'Mã QR không chứa thông tin tài sản hợp lệ';
                cameraStatus.style.color = '#ff9800';
                
                // Cho phép quét tiếp sau 1.5 giây
                setTimeout(() => {
                    scannerFrame.classList.remove('success-scan');
                    scannerActive = true;
                }, 1500);
            }
        } catch (e) {
            console.error('Lỗi khi xử lý URL từ mã QR:', e);
            cameraStatus.textContent = 'Mã QR chứa URL không hợp lệ';
            cameraStatus.style.color = '#ff9800';
            
            // Cho phép quét tiếp sau 1.5 giây
            setTimeout(() => {
                scannerFrame.classList.remove('success-scan');
                scannerActive = true;
            }, 1500);
        }
    }
    
    // Phát âm thanh khi quét thành công
    function playSuccessSound() {
        try {
            const audio = new Audio('data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjI5LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAAFWgD///////////////////////////////////////////8AAAA8TEFNRTMuMTAwAc0AAAAAAAAAABSAJAOkQgAAgAAABVrYn9GcAAAAAAAAAAAAAAAAAAAA//vQZAAAAaYTV4UEQAIdYgufQBUABHRDX/T2kAB8CHLunNIAJeMGwZFW8/4P//h/UH/gg88f//yP6Tf//IIODhw4OAECBAgAAAYcHDk3OOf4sUUWAYYHGC4pJkiDDgwQYJiYmKIMMDwfBwMDN4mKKB8vy+D/+fthQ/8uKJ//lw//+Sf4IOg/5c//+XB8uB8Hg4Hg+D/Lg////+bS7///L/y4f//wo8v//Lg8H/lw/8v//Lg///+DDDD0MP8swwwwDDDAwIMMMA86kz///Jv/4MfL5f+XtL5f//L2l/5e0vg+f+X+X5cP/lw+D4PL2l//5cP8uHy/L5f/gy//+X/+DDBkICf/KBAXf44Fg+XyQIF3/KB//5EP///8iH///yIf//5EP//8AACAAAEAYYYYYYEFDDDCYYAAYYICoOgYIKgcHwcBkpxDQ0wfB4PkVhGH/++BSfjj/BQOP8Hx//ygcfKBAJH///8CgeUDj/Lg+BwQOP5QIHlA44/wfBwQOPlAgEDyEQOOUCBxwQOP8HwcHAMMP8EDg4BBgQQYaBgeUDgYEDj/BAYaB5QPKBBBB5QOOPKBx8oHlAgcf4IBgoHH+UDj5QOPkDgYiBxwQOBgcf4Plx/gjnVW1QLK5WIpasgIpZbQYSCWyBRQDbQ0lFIpFJmrVYKNsLBwsmBBgsfzjFbqTGLpWsQiINYgxSBGJidXSm7r1mKiCaTCyBRIDtTWIKSEFi5Kx1INZZ');
            audio.volume = 0.3;
            audio.play().catch(e => console.log('Không thể phát âm thanh:', e));
        } catch (e) {
            console.log('Không hỗ trợ phát âm thanh');
        }
    }
    
    // Đổi camera (trước/sau)
    switchCameraButton.addEventListener('click', function() {
        facingMode = facingMode === 'environment' ? 'user' : 'environment';
        
        // Cập nhật text của nút
        if (facingMode === 'user') {
            switchCameraButton.innerHTML = '<i class="fas fa-sync-alt"></i> Camera sau';
        } else {
            switchCameraButton.innerHTML = '<i class="fas fa-sync-alt"></i> Camera trước';
        }
        
        // Hiệu ứng nhấn nút
        switchCameraButton.classList.add('button-pressed');
        setTimeout(() => {
            switchCameraButton.classList.remove('button-pressed');
        }, 200);
        
        startCamera();
    });
    
    // Bật/tắt đèn flash
    toggleFlashButton.addEventListener('click', function() {
        if (!flashlight) return;
        
        const isOn = toggleFlashButton.classList.contains('active');
        try {
            flashlight.applyConstraints({
                advanced: [{ torch: !isOn }]
            }).then(() => {
                if (!isOn) {
                    toggleFlashButton.classList.add('active');
                    toggleFlashButton.innerHTML = '<i class="fas fa-bolt"></i> Tắt đèn';
                } else {
                    toggleFlashButton.classList.remove('active');
                    toggleFlashButton.innerHTML = '<i class="fas fa-bolt"></i> Đèn flash';
                }
            }).catch(err => {
                console.error('Lỗi khi điều khiển đèn flash:', err);
                if (window.notifySystem) {
                    window.notifySystem.warning('Thông báo', 'Không thể điều khiển đèn flash của camera.');
                }
            });
        } catch (err) {
            console.error('Lỗi khi điều khiển đèn flash:', err);
        }
    });
    
    // Thử lại khi có lỗi
    retryButton.addEventListener('click', function() {
        // Hiệu ứng nhấn nút
        retryButton.classList.add('button-pressed');
        setTimeout(() => {
            retryButton.classList.remove('button-pressed');
        }, 200);
        
        // Làm mới kết nối camera
        startCamera();
    });
    
    // Hàm debounce để tránh gọi nhiều lần
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func.apply(context, args);
            }, wait);
        };
    }
    
    // Điều chỉnh khi thay đổi hướng màn hình
    window.addEventListener('resize', debounce(function() {
        // Cập nhật flag desktop/mobile
        isDesktop = window.innerWidth >= 768;
        
        if (scannerActive && currentStream) {
            // Chỉ khởi động lại camera nếu kích thước thay đổi đáng kể
            const width = window.innerWidth;
            const height = window.innerHeight;
            const oldRatio = width / height;
            
            // Theo dõi sự thay đổi từ portrait sang landscape và ngược lại
            setTimeout(() => {
                const newWidth = window.innerWidth;
                const newHeight = window.innerHeight;
                const newRatio = newWidth / newHeight;
                
                // Nếu tỷ lệ thay đổi đáng kể (chuyển hướng màn hình)
                if (Math.abs(newRatio - oldRatio) > 0.2) {
                    console.log('Điều chỉnh camera theo hướng màn hình mới');
                    startCamera();
                }
            }, 300);
        }
    }, 500));
    
    // Xử lý lỗi cho iOS Safari
    if (/iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream) {
        video.setAttribute('playsinline', 'true');
        
        // Thêm hướng dẫn đặc biệt cho iOS
        if (errorContainer.style.display === 'none') {
            const iosNote = document.createElement('div');
            iosNote.className = 'instructions ios-note';
            iosNote.innerHTML = '<i class="fas fa-info-circle"></i> Đối với thiết bị iOS: Nếu gặp vấn đề với camera, hãy đảm bảo bạn đã cấp quyền trong Cài đặt &gt; Safari &gt; Camera.';
            document.querySelector('.scanner-controls').after(iosNote);
        }
    }
    
    // Thêm chức năng mới cho Desktop: Tải lên ảnh có QR code
    if (isDesktop) {
        // Thêm nút tải lên ảnh QR
        const uploadButton = document.createElement('button');
        uploadButton.className = 'btn-switch-camera';
        uploadButton.innerHTML = '<i class="fas fa-upload"></i> Tải ảnh QR';
        uploadButton.style.backgroundColor = '#7e57c2';
        
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.style.display = 'none';
        document.body.appendChild(fileInput);
        
        uploadButton.addEventListener('click', function() {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                const file = e.target.files[0];
                loadingIndicator.style.display = 'flex';
                
                const reader = new FileReader();
                reader.onload = function(event) {
                    const img = new Image();
                    img.onload = function() {
                        const canvas = document.createElement('canvas');
                        const context = canvas.getContext('2d');
                        canvas.width = img.width;
                        canvas.height = img.height;
                        context.drawImage(img, 0, 0, img.width, img.height);
                        
                        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                        const code = jsQR(imageData.data, imageData.width, imageData.height);
                        
                        loadingIndicator.style.display = 'none';
                        
                        if (code) {
                            handleQRCode(code.data);
                        } else {
                            cameraStatus.textContent = 'Không tìm thấy mã QR trong ảnh';
                            cameraStatus.style.color = '#f44336';
                        }
                    };
                    img.src = event.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
        
        document.querySelector('.scanner-controls').appendChild(uploadButton);
    }
    
    // Khởi động camera khi trang đã sẵn sàng
    startCamera();
});