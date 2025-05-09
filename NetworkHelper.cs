using System;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;

namespace Project_QLTS_DNC.Helpers
{
    public static class NetworkHelper
    {
        /// <summary>
        /// Trả về URL cơ sở của hệ thống
        /// </summary>
        /// <param name="port">Cổng dịch vụ (mặc định: 8080)</param>
        /// <returns>URL đầy đủ với tên miền</returns>
        public static string GetBaseUrl(int port = 8080)
        {
            try
            {
                // Sử dụng tên miền thay vì IP
                string domain = "thanhdatdnc.id.vn";
                return $"https://{domain}";  // Sử dụng HTTPS thay vì HTTP
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Lỗi khi lấy địa chỉ URL: {ex.Message}");
                return $"http://localhost:{port}";
            }
        }

        /// <summary>
        /// Phương thức dự phòng để tìm IPv4 đang được sử dụng cho kết nối mạng
        /// (Giữ lại để tham khảo hoặc sử dụng trong trường hợp cần)
        /// </summary>
        /// <returns>Địa chỉ IPv4 hoạt động</returns>
        private static string GetActiveIPv4()
        {
            string output = string.Empty;

            // Lấy tất cả các network interface đang hoạt động và không phải loopback
            NetworkInterface[] adapters = NetworkInterface.GetAllNetworkInterfaces();
            foreach (NetworkInterface adapter in adapters)
            {
                // Chỉ lấy các adapter đang UP và không phải loopback
                if (adapter.OperationalStatus == OperationalStatus.Up &&
                    adapter.NetworkInterfaceType != NetworkInterfaceType.Loopback)
                {
                    // Lấy các địa chỉ IP từ adapter đang xét
                    IPInterfaceProperties adapterProperties = adapter.GetIPProperties();
                    UnicastIPAddressInformationCollection allAddresses = adapterProperties.UnicastAddresses;

                    foreach (UnicastIPAddressInformation address in allAddresses)
                    {
                        // Chỉ lấy IPv4, không phải loopback và không phải địa chỉ nội bộ 169.254.x.x
                        if (address.Address.AddressFamily == AddressFamily.InterNetwork &&
                            !IPAddress.IsLoopback(address.Address) &&
                            !address.Address.ToString().StartsWith("169.254."))
                        {
                            return address.Address.ToString();
                        }
                    }
                }
            }

            // Fallback: Cách khác để tìm địa chỉ IP
            using (Socket socket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, 0))
            {
                try
                {
                    // Kết nối đến một địa chỉ bất kỳ (8.8.8.8 - Google DNS)
                    socket.Connect("8.8.8.8", 65530);
                    IPEndPoint endPoint = socket.LocalEndPoint as IPEndPoint;
                    if (endPoint != null)
                    {
                        return endPoint.Address.ToString();
                    }
                }
                catch
                {
                    // Bỏ qua lỗi
                }
            }

            return output;
        }
    }
}