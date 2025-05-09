using System;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using System.Collections.Generic;
using Project_QLTS_DNC.Services.QLTaiSanService;
using Project_QLTS_DNC.Helpers;

namespace Project_QLTS_DNC.DTOs
{
    // Static class to hold shared cache data
    public static class TaiSanQRDTOCache
    {
        public static Dictionary<int, string> NhomTSNames { get; } = new Dictionary<int, string>();
    }

    public class TaiSanQRDTO : TaiSanDTO
    {
        private int? _maNhomTS;
        private string _tenNhomTS;
        private string _maQrUrl;

        // Cache đã tải thông tin nhóm tài sản hay chưa
        private bool _hasLoadedGroupInfo = false;

        // Mã nhóm tài sản
        public new int? MaNhomTS
        {
            get { return _maNhomTS; }
            set
            {
                if (_maNhomTS != value)
                {
                    _maNhomTS = value;
                    OnPropertyChanged(nameof(MaNhomTS));
                }
            }
        }

        // Tên nhóm tài sản
        public new string TenNhomTS
        {
            get { return _tenNhomTS; }
            set
            {
                if (_tenNhomTS != value)
                {
                    _tenNhomTS = value;
                    OnPropertyChanged(nameof(TenNhomTS));
                }
            }
        }

        // URL cho mã QR (có thể là URL website hoặc dữ liệu JSON)
        public string MaQrUrl
        {
            get { return _maQrUrl; }
            set
            {
                if (_maQrUrl != value)
                {
                    _maQrUrl = value;
                    OnPropertyChanged(nameof(MaQrUrl));
                }
            }
        }

        // Constructor copy từ TaiSanDTO
        public static TaiSanQRDTO FromTaiSanDTO(TaiSanDTO taiSanDTO)
        {
            var qrDTO = new TaiSanQRDTO
            {
                MaTaiSan = taiSanDTO.MaTaiSan,
                MaChiTietPN = taiSanDTO.MaChiTietPN,
                TenTaiSan = taiSanDTO.TenTaiSan,
                SoSeri = taiSanDTO.SoSeri,
                MaQR = taiSanDTO.MaQR,
                NgaySuDung = taiSanDTO.NgaySuDung,
                HanBH = taiSanDTO.HanBH,
                TinhTrangSP = taiSanDTO.TinhTrangSP,
                GhiChu = taiSanDTO.GhiChu,
                MaPhong = taiSanDTO.MaPhong,
                TenPhong = taiSanDTO.TenPhong,
                IsSelected = taiSanDTO.IsSelected
            };

            // Kế thừa thông tin nhóm tài sản nếu có
            if (taiSanDTO.MaNhomTS.HasValue)
            {
                qrDTO.MaNhomTS = taiSanDTO.MaNhomTS;
                qrDTO.TenNhomTS = taiSanDTO.TenNhomTS;
                qrDTO._hasLoadedGroupInfo = true;
            }

            // Tạo URL với tên miền cho QR code
            string baseUrl = NetworkHelper.GetBaseUrl();
            qrDTO.MaQrUrl = $"{baseUrl}/qr?id={qrDTO.MaTaiSan}&seri={qrDTO.SoSeri}";

            return qrDTO;
        }

        // Tối ưu hóa phương thức LoadNhomTaiSanInfoAsync
        public async Task LoadNhomTaiSanInfoAsync()
        {
            // Kiểm tra xem đã tải thông tin nhóm tài sản chưa
            if (_hasLoadedGroupInfo || !MaChiTietPN.HasValue)
                return;

            try
            {
                var chiTietPN = await ChiTietPhieuNhapService.LayChiTietPhieuNhapTheoMaAsync(MaChiTietPN.Value);
                MaNhomTS = chiTietPN.MaNhomTS;

                // Lấy tên nhóm tài sản từ cache nếu có
                if (TaiSanQRDTOCache.NhomTSNames.TryGetValue(MaNhomTS.Value, out string tenNhom))
                {
                    TenNhomTS = tenNhom;
                }
                else
                {
                    // Nếu không có trong cache, tải từ database
                    var nhomTSList = await NhomTaiSanService.LayDanhSachNhomTaiSanAsync();
                    var nhomTS = nhomTSList.FirstOrDefault(n => n.MaNhomTS == MaNhomTS);
                    if (nhomTS != null)
                    {
                        TenNhomTS = nhomTS.TenNhom;

                        // Lưu vào cache
                        TaiSanQRDTOCache.NhomTSNames[MaNhomTS.Value] = nhomTS.TenNhom;
                    }
                }

                _hasLoadedGroupInfo = true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Lỗi khi tải thông tin nhóm tài sản: {ex.Message}");
            }
        }
    }
}