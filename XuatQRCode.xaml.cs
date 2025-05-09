using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;
using ZXing;
using ZXing.Common;
using ZXing.QrCode;
using ZXing.QrCode.Internal;
using ZXing.Rendering;
using System.Drawing;
using System.Drawing.Imaging;
using iTextImage = iText.Layout.Element.Image;
using iText.IO.Image;
using iText.Kernel.Pdf;
using iText.Layout;
using iText.Layout.Element;
using iText.Layout.Properties;
using iTextErrorCorrectionLevel = iText.Barcodes.Qrcode.ErrorCorrectionLevel;
using ZXingErrorCorrectionLevel = ZXing.QrCode.Internal.ErrorCorrectionLevel;
using Project_QLTS_DNC.DTOs;
using Project_QLTS_DNC.Services.QLTaiSanService;
using System.Windows.Input;
using iTextTextAlignment = iText.Layout.Properties.TextAlignment;
using System.ComponentModel;
using System.Diagnostics;
using Project_QLTS_DNC.Helpers;
using Project_QLTS_DNC.Services.QLToanNha;
using Project_QLTS_DNC.Models.QLTaiSan;
using Project_QLTS_DNC.Models.QLNhomTS;
using Project_QLTS_DNC.Services;
using Supabase.Postgrest.Interfaces;

namespace Project_QLTS_DNC.View.QuanLySanPham
{
    public class BitmapRenderer : ZXing.Rendering.IBarcodeRenderer<Bitmap>
    {
        public Bitmap Render(BitMatrix matrix, BarcodeFormat format, string content)
        {
            return Render(matrix, format, content, new EncodingOptions());
        }

        public Bitmap Render(BitMatrix matrix, BarcodeFormat format, string content, EncodingOptions options)
        {
            int width = matrix.Width;
            int height = matrix.Height;

            Bitmap bitmap = new Bitmap(width, height, System.Drawing.Imaging.PixelFormat.Format32bppArgb);

            for (int x = 0; x < width; x++)
            {
                for (int y = 0; y < height; y++)
                {
                    bitmap.SetPixel(x, y, matrix[x, y] ? Color.Black : Color.White);
                }
            }

            return bitmap;
        }
    }

    public partial class XuatQRCode : Window
    {
        private ObservableCollection<TaiSanQRDTO> _listTaiSan;
        private ObservableCollection<TaiSanQRDTO> _filteredTaiSan;
        private List<NhomTaiSanFilter> _nhomTSList;
        private List<PhongFilter> _phongList;
        private int _totalItems = 0;
        private int _selectedItems = 0;

        // Biến quản lý phân trang
        private int _pageSize = 11; // Số lượng tài sản hiển thị trên mỗi trang
        private int _currentPage = 1; // Trang hiện tại
        private int _totalPages = 1; // Tổng số trang
        private List<TaiSanQRDTO> _currentPageItems; // Các item trên trang hiện tại

        // Thêm một cache để lưu thông tin liên quan
        private Dictionary<int, int> _chiTietPNCache = new Dictionary<int, int>();
        private Dictionary<int, string> _nhomTSCache = new Dictionary<int, string>();

        public XuatQRCode(ObservableCollection<TaiSanDTO> dsTaiSan = null)
        {
            InitializeComponent();

            // Cho phép di chuyển cửa sổ bằng cách kéo từ bất kỳ đâu
            this.MouseLeftButtonDown += (s, e) => { this.DragMove(); };

            // Đăng ký events
            btnCancel.Click += BtnCancel_Click;
            btnExportQR.Click += BtnExportQR_Click;
            btnSelectAll.Click += BtnSelectAll_Click;
            btnUnselectAll.Click += BtnUnselectAll_Click;
            btnApplyFilter.Click += BtnApplyFilter_Click;
            txtSearchSeri.TextChanged += TxtSearchSeri_TextChanged;
            cboNhomTS.SelectionChanged += Filter_SelectionChanged;
            cboPhong.SelectionChanged += Filter_SelectionChanged;

            // Đăng ký sự kiện phân trang
            btnPreviousPage.Click += BtnPreviousPage_Click;
            btnNextPage.Click += BtnNextPage_Click;
            txtCurrentPage.KeyDown += TxtCurrentPage_KeyDown;

            // Tải dữ liệu
            InitializeDataAsync(dsTaiSan);
        }

        private async void InitializeDataAsync(ObservableCollection<TaiSanDTO> dsTaiSan)
        {
            try
            {
                // Hiển thị con trỏ đang tải
                Mouse.OverrideCursor = Cursors.Wait;

                // Tải song song danh sách nhóm tài sản và phòng để tăng tốc
                var nhomTSTask = LoadNhomTaiSanAsync();
                var phongTask = LoadPhongAsync();

                // Chờ cả hai tác vụ hoàn thành
                await Task.WhenAll(nhomTSTask, phongTask);

                // Khởi tạo dữ liệu tài sản
                await InitializeAssetDataAsync(dsTaiSan);

                // Cập nhật thông tin phân trang
                UpdatePagingInfo();

                // Áp dụng phân trang và cập nhật giao diện
                ApplyPaging();
                UpdatePagingUI();

                // Cập nhật trạng thái
                _totalItems = _filteredTaiSan.Count;
                UpdateStatusText();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi khi tải dữ liệu: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                // Trả lại con trỏ bình thường
                Mouse.OverrideCursor = null;
            }
        }

        // Tối ưu hóa hàm khởi tạo dữ liệu tài sản
        private async Task InitializeAssetDataAsync(ObservableCollection<TaiSanDTO> dsTaiSan)
        {
            // Nếu không có dữ liệu được truyền vào, tải từ service
            if (dsTaiSan == null || dsTaiSan.Count == 0)
            {
                // Tải toàn bộ danh sách tài sản - giữ lại phương pháp cũ
                var taiSanModels = await TaiSanService.LayDanhSachTaiSanAsync();
                _listTaiSan = new ObservableCollection<TaiSanQRDTO>(
                    taiSanModels.Select(model => TaiSanQRDTO.FromTaiSanDTO(TaiSanDTO.FromModel(model))));

                // Tải thông tin nhóm tài sản theo batch
                await LoadAssetGroupInfoBatchAsync(_listTaiSan);
            }
            else
            {
                // Sử dụng dữ liệu đã truyền vào
                _listTaiSan = new ObservableCollection<TaiSanQRDTO>(
                    dsTaiSan.Select(dto => TaiSanQRDTO.FromTaiSanDTO(dto)));

                // Tải thông tin nhóm tài sản theo batch
                await LoadAssetGroupInfoBatchAsync(_listTaiSan);
            }

            // Khởi tạo danh sách đã lọc với tất cả các tài sản
            _filteredTaiSan = new ObservableCollection<TaiSanQRDTO>(_listTaiSan);
        }

        // Tải thông tin nhóm tài sản theo batch thay vì từng tài sản một
        private async Task LoadAssetGroupInfoBatchAsync(ObservableCollection<TaiSanQRDTO> assets)
        {
            try
            {
                // Lấy tất cả các MaChiTietPN duy nhất
                var chiTietPNIds = assets
                    .Where(a => a.MaChiTietPN.HasValue)
                    .Select(a => a.MaChiTietPN.Value)
                    .Distinct()
                    .ToList();

                if (chiTietPNIds.Count == 0)
                    return;

                // Tải tất cả ChiTietPhieuNhap trong một truy vấn
                var client = await SupabaseService.GetClientAsync();

                // Xây dựng filter cho nhiều ID
                var chiTietPNs = await client.From<ChiTietPhieuNhap>()
                    .Where(c => chiTietPNIds.Contains(c.MaChiTietPN))
                    .Get();

                // Tạo lookup dictionary cho ChiTietPhieuNhap
                var chiTietPNDict = chiTietPNs.Models.ToDictionary(c => c.MaChiTietPN);

                // Lấy tất cả các MaNhomTS duy nhất
                var nhomTSIds = chiTietPNs.Models.Select(c => c.MaNhomTS).Distinct().ToList();

                if (nhomTSIds.Count == 0)
                    return;

                // Tải tất cả NhomTaiSan trong một truy vấn
                var nhomTSs = await client.From<NhomTaiSan>()
                    .Where(n => nhomTSIds.Contains(n.MaNhomTS))
                    .Get();

                // Tạo lookup dictionary cho NhomTaiSan
                var nhomTSDict = nhomTSs.Models.ToDictionary(n => n.MaNhomTS);

                // Cập nhật thông tin nhóm cho tất cả tài sản
                foreach (var asset in assets)
                {
                    if (asset.MaChiTietPN.HasValue && chiTietPNDict.TryGetValue(asset.MaChiTietPN.Value, out var chiTietPN))
                    {
                        asset.MaNhomTS = chiTietPN.MaNhomTS;

                        if (nhomTSDict.TryGetValue(chiTietPN.MaNhomTS, out var nhomTS))
                        {
                            asset.TenNhomTS = nhomTS.TenNhom;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Lỗi khi tải thông tin nhóm tài sản: {ex.Message}");
            }
        }

        private async Task LoadNhomTaiSanAsync()
        {
            try
            {
                _nhomTSList = await NhomTaiSanService.GetNhomTaiSanFilterListAsync();
                cboNhomTS.ItemsSource = _nhomTSList;
                cboNhomTS.SelectedIndex = 0; // Chọn "Tất cả" mặc định
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi khi tải danh sách nhóm tài sản: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async Task LoadPhongAsync()
        {
            try
            {
                // Lấy danh sách phòng từ service
                var phongCollection = await PhongService.LayDanhSachPhongAsync();

                // Tạo danh sách PhongFilter từ dữ liệu phòng
                _phongList = new List<PhongFilter>
                {
                    new PhongFilter { MaPhong = null, TenPhong = "Tất cả" }
                };

                // Thêm các phòng từ cơ sở dữ liệu vào danh sách
                foreach (var phong in phongCollection)
                {
                    _phongList.Add(new PhongFilter
                    {
                        MaPhong = phong.MaPhong,
                        TenPhong = phong.TenPhong
                    });
                }

                // Gán danh sách phòng cho ComboBox
                cboPhong.ItemsSource = _phongList;
                cboPhong.SelectedIndex = 0; // Chọn "Tất cả" mặc định
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi khi tải danh sách phòng: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        // Tối ưu hóa ApplyFilters để áp dụng bộ lọc hiệu quả hơn
        private void ApplyFilters()
        {
            try
            {
                Mouse.OverrideCursor = Cursors.Wait;

                string searchText = txtSearchSeri.Text.ToLower().Trim();
                int? selectedNhomTS = cboNhomTS.SelectedIndex > 0 ? ((NhomTaiSanFilter)cboNhomTS.SelectedItem).MaNhomTS : null;
                int? selectedPhong = cboPhong.SelectedIndex > 0 ? ((PhongFilter)cboPhong.SelectedItem).MaPhong : null;

                // Lọc dữ liệu ở phía client
                ApplyClientSideFilters(searchText, selectedNhomTS, selectedPhong);

                // Cập nhật thông tin phân trang
                _currentPage = 1; // Reset về trang đầu tiên khi lọc
                UpdatePagingInfo();

                // Áp dụng phân trang và cập nhật giao diện
                ApplyPaging();
                UpdatePagingUI();

                // Cập nhật trạng thái
                _totalItems = _filteredTaiSan.Count;
                _selectedItems = _currentPageItems.Count(item => item.IsSelected);
                UpdateStatusText();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Lỗi khi áp dụng bộ lọc: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                Mouse.OverrideCursor = null;
            }
        }

        // Lọc dữ liệu ở phía client - hiệu quả với dữ liệu nhỏ
        private void ApplyClientSideFilters(string searchText, int? nhomTSId, int? phongId)
        {
            var filteredItems = _listTaiSan.AsParallel().Where(ts =>
                (string.IsNullOrEmpty(searchText) ||
                (ts.SoSeri != null && ts.SoSeri.ToLower().Contains(searchText)) ||
                (ts.TenTaiSan != null && ts.TenTaiSan.ToLower().Contains(searchText))) &&
                (!nhomTSId.HasValue || ts.MaNhomTS == nhomTSId) &&
                (!phongId.HasValue || ts.MaPhong == phongId)
            ).ToList();

            // Cập nhật danh sách đã lọc
            _filteredTaiSan.Clear();
            foreach (var item in filteredItems)
            {
                _filteredTaiSan.Add(item);
            }
        }

        private void Filter_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            // Áp dụng filter khi thay đổi combobox
            if (IsInitialized && _filteredTaiSan != null)
            {
                // Reset về trang đầu tiên khi thay đổi bộ lọc
                _currentPage = 1;
                ApplyFilters();
            }
        }

        private void TxtSearchSeri_TextChanged(object sender, TextChangedEventArgs e)
        {
            // Không cần apply filter ngay khi nhập, chỉ khi nhấn nút "Áp dụng" hoặc enter
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            this.DialogResult = false;
            this.Close();
        }

        private void BtnApplyFilter_Click(object sender, RoutedEventArgs e)
        {
            // Reset về trang đầu tiên khi áp dụng bộ lọc
            _currentPage = 1;
            ApplyFilters();
        }

        private void BtnSelectAll_Click(object sender, RoutedEventArgs e)
        {
            // Chọn tất cả các item trên trang hiện tại
            foreach (var item in _currentPageItems)
            {
                item.IsSelected = true;
            }

            // Cập nhật số lượng đã chọn
            _selectedItems = _filteredTaiSan.Count(item => item.IsSelected);
            UpdateStatusText();
        }

        private void BtnUnselectAll_Click(object sender, RoutedEventArgs e)
        {
            // Bỏ chọn tất cả các item trên trang hiện tại
            foreach (var item in _currentPageItems)
            {
                item.IsSelected = false;
            }

            // Cập nhật số lượng đã chọn
            _selectedItems = _filteredTaiSan.Count(item => item.IsSelected);
            UpdateStatusText();
        }

        private void UpdateStatusText()
        {
            txtStatus.Text = $"Đã chọn: {_selectedItems} / {_totalItems} sản phẩm";
        }

        private void CheckBox_Changed(object sender, RoutedEventArgs e)
        {
            _selectedItems = _filteredTaiSan.Count(item => item.IsSelected);
            UpdateStatusText();
        }

        private void BtnExportQR_Click(object sender, RoutedEventArgs e)
        {
            var selectedItems = _filteredTaiSan.Where(item => item.IsSelected).ToList();

            if (selectedItems.Count == 0)
            {
                MessageBox.Show("Vui lòng chọn ít nhất một sản phẩm để xuất mã QR.", "Thông báo", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            SaveFileDialog saveFileDialog = new SaveFileDialog
            {
                Filter = "PDF Files (*.pdf)|*.pdf",
                FileName = "QRCode_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + ".pdf"
            };

            if (saveFileDialog.ShowDialog() == true)
            {
                try
                {
                    Mouse.OverrideCursor = Cursors.Wait;

                    string filePath = saveFileDialog.FileName;

                    // Đảm bảo thư mục đích tồn tại
                    string directoryPath = Path.GetDirectoryName(filePath);
                    if (!Directory.Exists(directoryPath))
                    {
                        Directory.CreateDirectory(directoryPath);
                    }

                    // Xuất file PDF
                    ExportQRCodeToPDF(filePath, selectedItems);

                    Mouse.OverrideCursor = null;

                    // Tạo và hiển thị thông báo thành công với SuccessNotificationDialog
                    var notificationDialog = new View.Common.SuccessNotificationDialog(
                        "Xuất mã QR thành công!",
                        $"File mã QR đã được xuất thành công và lưu tại:\n{filePath}",
                        filePath);

                    // SuccessNotificationDialog đã có sẵn sự kiện BtnOpenFile.Click 
                    // trong class của nó, ta không cần gán thêm event handler
                    notificationDialog.Show();
                }
                catch (Exception ex)
                {
                    Mouse.OverrideCursor = null;

                    // Ghi log lỗi
                    LogError(ex);

                    // Hiển thị thông báo lỗi chi tiết
                    MessageBox.Show(
                        $"Lỗi khi xuất mã QR: {ex.Message}\n\nChi tiết lỗi: {ex.StackTrace}",
                        "Lỗi",
                        MessageBoxButton.OK,
                        MessageBoxImage.Error);
                }
            }
        }

        #region Phân trang

        private void UpdatePagingInfo()
        {
            // Tính tổng số trang
            _totalItems = _filteredTaiSan.Count;
            _totalPages = (_totalItems + _pageSize - 1) / _pageSize; // Công thức làm tròn lên

            // Đảm bảo trang hiện tại không vượt quá tổng số trang
            if (_currentPage > _totalPages)
            {
                _currentPage = _totalPages > 0 ? _totalPages : 1;
            }
        }

        private void ApplyPaging()
        {
            // Tính chỉ số bắt đầu và kết thúc cho trang hiện tại
            int startIndex = (_currentPage - 1) * _pageSize;

            // Lấy các tài sản cho trang hiện tại
            _currentPageItems = _filteredTaiSan
                .Skip(startIndex)
                .Take(_pageSize)
                .ToList();

            // Cập nhật nguồn dữ liệu cho DataGrid
            dgSanPham.ItemsSource = _currentPageItems;
        }

        private void UpdatePagingUI()
        {
            // Cập nhật số trang hiện tại và tổng số trang trong UI
            txtCurrentPage.Text = _currentPage.ToString();
            txtTotalPages.Text = _totalPages.ToString();

            // Cập nhật trạng thái nút phân trang
            btnPreviousPage.IsEnabled = _currentPage > 1;
            btnNextPage.IsEnabled = _currentPage < _totalPages;
        }

        private void BtnPreviousPage_Click(object sender, RoutedEventArgs e)
        {
            if (_currentPage > 1)
            {
                _currentPage--;
                ApplyPaging();
                UpdatePagingUI();

                // Cập nhật số lượng đã chọn
                _selectedItems = _filteredTaiSan.Count(item => item.IsSelected);
                UpdateStatusText();
            }
        }

        private void BtnNextPage_Click(object sender, RoutedEventArgs e)
        {
            if (_currentPage < _totalPages)
            {
                _currentPage++;
                ApplyPaging();
                UpdatePagingUI();

                // Cập nhật số lượng đã chọn
                _selectedItems = _filteredTaiSan.Count(item => item.IsSelected);
                UpdateStatusText();
            }
        }

        private void TxtCurrentPage_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                try
                {
                    int newPage = int.Parse(txtCurrentPage.Text);
                    if (newPage > 0 && newPage <= _totalPages)
                    {
                        _currentPage = newPage;
                        ApplyPaging();
                        UpdatePagingUI();

                        // Cập nhật số lượng đã chọn
                        _selectedItems = _filteredTaiSan.Count(item => item.IsSelected);
                        UpdateStatusText();
                    }
                    else
                    {
                        // Nếu số trang không hợp lệ, đặt lại giá trị cũ
                        txtCurrentPage.Text = _currentPage.ToString();
                    }
                }
                catch
                {
                    // Nếu nhập không phải số, đặt lại giá trị cũ
                    txtCurrentPage.Text = _currentPage.ToString();
                }
            }
        }

        #endregion

        // Phương thức mở file PDF với xử lý ngoại lệ chi tiết
        // Phương thức mở file PDF với xử lý ngoại lệ và phương pháp thay thế
        private void OpenPdfFile(string filePath)
        {
            try
            {
                // Kiểm tra file tồn tại trước
                if (!File.Exists(filePath))
                {
                    MessageBox.Show("File không tồn tại.", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
                    return;
                }

                try
                {
                    // Phương pháp 1: Sử dụng Process.Start với ProcessStartInfo
                    ProcessStartInfo startInfo = new ProcessStartInfo
                    {
                        FileName = filePath,
                        UseShellExecute = true
                    };
                    System.Diagnostics.Process.Start(startInfo);
                }
                catch (Win32Exception ex)
                {
                    // Ghi log lỗi từ phương pháp 1
                    LogError(new Exception($"Lỗi phương pháp 1: {ex.Message}", ex));

                    try
                    {
                        // Phương pháp 2: Sử dụng shell execute
                        System.Diagnostics.Process.Start("explorer.exe", $"\"{filePath}\"");
                    }
                    catch (Exception explorerEx)
                    {
                        // Ghi log lỗi từ phương pháp 2
                        LogError(new Exception($"Lỗi phương pháp 2: {explorerEx.Message}", explorerEx));

                        try
                        {
                            // Phương pháp 3: Sử dụng rundll32
                            System.Diagnostics.Process.Start("rundll32.exe", $"shell32.dll,ShellExec_RunDLL \"{filePath}\"");
                        }
                        catch (Exception rundllEx)
                        {
                            // Ghi log lỗi từ phương pháp 3
                            LogError(new Exception($"Lỗi phương pháp 3: {rundllEx.Message}", rundllEx));

                            // Nếu tất cả các phương pháp đều thất bại, thông báo cho người dùng
                            MessageBox.Show(
                                $"Không thể mở file. Vui lòng thử mở file thủ công tại đường dẫn:\n{filePath}",
                                "Lỗi",
                                MessageBoxButton.OK,
                                MessageBoxImage.Error);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                LogError(ex);
                MessageBox.Show($"Lỗi không xác định khi mở file: {ex.Message}", "Lỗi", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        // Phương thức ghi log lỗi
        private void LogError(Exception ex)
        {
            try
            {
                string logPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "QRCodeError.log");
                string errorMessage = $"Thời gian: {DateTime.Now}\n" +
                                      $"Lỗi: {ex.Message}\n" +
                                      $"Chi tiết: {ex.ToString()}\n" +
                                      $"Nguồn: {ex.Source}\n" +
                                      $"Ngăn xếp: {ex.StackTrace}\n" +
                                      "---------------------------------------------------\n";

                File.AppendAllText(logPath, errorMessage);
            }
            catch
            {
                // Nếu không thể ghi log, bỏ qua để tránh gây thêm lỗi
            }
        }

        // Nội dung phương thức ExportQRCodeToPDF
        private void ExportQRCodeToPDF(string filePath, List<TaiSanQRDTO> selectedItems)
        {
            using (PdfWriter writer = new PdfWriter(filePath))
            {
                using (PdfDocument pdf = new PdfDocument(writer))
                {
                    Document document = new Document(pdf);
                    iText.Layout.Element.Table table = new iText.Layout.Element.Table(2);
                    table.SetWidth(UnitValue.CreatePercentValue(100));

                    int cellCount = 0;

                    // Lấy base URL từ NetworkHelper
                    string baseUrl = NetworkHelper.GetBaseUrl();

                    foreach (var item in selectedItems)
                    {
                        // Tạo mã QR với tên miền
                        string qrContent = $"{baseUrl}/qr?id={item.MaTaiSan}&seri={item.SoSeri}";

                        // Tạo QR code với độ phân giải và error correction cao hơn
                        BarcodeWriter<Bitmap> barcodeWriter = new BarcodeWriter<Bitmap>();
                        barcodeWriter.Format = BarcodeFormat.QR_CODE;
                        barcodeWriter.Options = new QrCodeEncodingOptions
                        {
                            Height = 400, // Tăng kích thước
                            Width = 400,
                            Margin = 1,
                            ErrorCorrection = ZXingErrorCorrectionLevel.H, // Độ chịu lỗi cao nhất
                            CharacterSet = "UTF-8"
                        };
                        barcodeWriter.Renderer = new BitmapRenderer();

                        using (Bitmap qrBitmap = barcodeWriter.Write(qrContent))
                        {
                            // Lưu QR code tạm thời vào một MemoryStream
                            using (MemoryStream ms = new MemoryStream())
                            {
                                qrBitmap.Save(ms, ImageFormat.Png);
                                byte[] imageBytes = ms.ToArray();

                                // Tạo cell cho mã QR
                                iText.Layout.Element.Cell cell = new iText.Layout.Element.Cell();
                                cell.SetPadding(10);
                                cell.SetBorder(iText.Layout.Borders.Border.NO_BORDER);

                                // Thêm hình ảnh mã QR vào cell
                                iTextImage qrImage = new iTextImage(ImageDataFactory.Create(imageBytes));
                                qrImage.SetWidth(UnitValue.CreatePercentValue(70));

                                // Use fully qualified iText TextAlignment to avoid ambiguity
                                qrImage.SetTextAlignment(iTextTextAlignment.CENTER);

                                // Tạo các dòng thông tin
                                Paragraph pTitle = new Paragraph("MÃ QR TÀI SẢN")
                                    .SetFontSize(12)
                                    .SetBold()
                                    .SetTextAlignment(iTextTextAlignment.CENTER);

                                Paragraph pTenTS = new Paragraph($"Tên TS: {item.TenTaiSan}")
                                    .SetFontSize(9);

                                Paragraph pMaTS = new Paragraph($"Mã TS: {item.MaTaiSan}")
                                    .SetFontSize(9);

                                Paragraph pSoSeri = new Paragraph($"Số Seri: {item.SoSeri}")
                                    .SetFontSize(9);

                                Paragraph pPhong = new Paragraph($"Phòng: {item.TenPhong ?? "Chưa phân phòng"}")
                                    .SetFontSize(9);

                                Paragraph pNhomTS = new Paragraph($"Nhóm TS: {item.TenNhomTS ?? "Không xác định"}")
                                    .SetFontSize(9);

                                // Thêm các thông tin vào cell
                                cell.Add(pTitle);
                                cell.Add(qrImage);
                                cell.Add(pTenTS);
                                cell.Add(pMaTS);
                                cell.Add(pSoSeri);
                                cell.Add(pPhong);
                                cell.Add(pNhomTS);

                                // Thêm cell vào bảng
                                table.AddCell(cell);

                                cellCount++;

                                // Mỗi khi đủ 4 cell (2x2), thêm bảng vào document và tạo bảng mới
                                if (cellCount % 4 == 0)
                                {
                                    document.Add(table);

                                    // Create a page break
                                    document.Add(new AreaBreak());

                                    table = new iText.Layout.Element.Table(2);
                                    table.SetWidth(UnitValue.CreatePercentValue(100));
                                }
                            }
                        }
                    }

                    // Nếu còn cell chưa được thêm vào document, thêm bảng cuối cùng
                    if (cellCount % 4 != 0)
                    {
                        // Thêm ô trống để đảm bảo đủ 4 ô
                        while (cellCount % 4 != 0)
                        {
                            iText.Layout.Element.Cell emptyCell = new iText.Layout.Element.Cell();
                            emptyCell.SetBorder(iText.Layout.Borders.Border.NO_BORDER);
                            table.AddCell(emptyCell);
                            cellCount++;
                        }
                        document.Add(table);
                    }
                }
            }
        }
    }
}