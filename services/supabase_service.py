from supabase import create_client
from config import Config
from datetime import datetime

class SupabaseService:
    """
    Dịch vụ quản lý kết nối đến Supabase
    """
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
            # Khởi tạo kết nối Supabase client
            cls._client = create_client(
                Config.SUPABASE_URL,
                Config.SUPABASE_API_KEY
            )
        return cls._instance
    
    @property
    def client(self):
        """Trả về Supabase client đã khởi tạo"""
        return self._client
    
    def get_assets(self, page=1, limit=10, search=None, group=None, status=None):
        """
        Lấy danh sách tài sản với phân trang và lọc
    
        Args:
            page: Trang hiện tại
            limit: Số lượng kết quả mỗi trang
            search: Từ khóa tìm kiếm
            group: Lọc theo nhóm tài sản
            status: Lọc theo tình trạng
        """
        offset = (page - 1) * limit
    
        # Bắt đầu query
        query = self._client.table('taisan') \
            .select('*, chitietphieunhap:ma_chi_tiet_pn(ten_tai_san, ma_nhom_ts, nhomtaisan:ma_nhom_ts(ten_nhom_ts, loaitaisan:ma_loai_ts(ten_loai_ts)))') \
            .limit(limit) \
            .offset(offset)
    
        # Thêm điều kiện tìm kiếm
        if search:
            query = query.or_(f'ten_tai_san.ilike.%{search}%, so_seri.ilike.%{search}%, ma_qr.ilike.%{search}%')
        
        # Lọc theo nhóm tài sản
        if group and group != 'all':
            # Không thể lọc trực tiếp, chúng ta sẽ lọc sau khi lấy dữ liệu
            pass
            
        # Lọc theo tình trạng
        if status and status != 'all':
            query = query.eq('tinh_trang_sp', status)
            
        # Thực thi query
        response = query.execute()
    
        # Đếm tổng số lượng kết quả (không phân trang)
        count_query = self._client.table('taisan').select('ma_tai_san', count='exact')
    
        # Thêm điều kiện tìm kiếm tương tự
        if search:
            count_query = count_query.or_(f'ten_tai_san.ilike.%{search}%, so_seri.ilike.%{search}%, ma_qr.ilike.%{search}%')
            
        if status and status != 'all':
            count_query = count_query.eq('tinh_trang_sp', status)
            
        count_response = count_query.execute()
    
        data = response.data
    
        # Lọc theo nhóm tài sản sau khi lấy dữ liệu
        if group and group != 'all':
            filtered_data = []
            for item in data:
                if item.get('chitietphieunhap') and \
                str(item['chitietphieunhap'].get('ma_nhom_ts')) == group:
                    filtered_data.append(item)
            data = filtered_data
    
        # Trả về kết quả và tổng số lượng
        return data, count_response.count
    
    def get_asset_by_id(self, asset_id):
        """
        Lấy thông tin chi tiết của tài sản theo ID
        
        Args:
            asset_id: ID của tài sản cần lấy
            
        Returns:
            Thông tin tài sản
        """
        response = self._client.table('taisan') \
            .select('*, chitietphieunhap:ma_chi_tiet_pn(ten_tai_san, ma_nhom_ts, nhomtaisan:ma_nhom_ts(ten_nhom_ts, loaitaisan:ma_loai_ts(ten_loai_ts))),phong:ma_phong(ten_phong)') \
            .eq('ma_tai_san', asset_id) \
            .execute()
            
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    def get_asset_specific_specifications(self, asset_id):
        """
        Lấy thông số riêng của tài sản
        
        Args:
            asset_id: ID của tài sản
            
        Returns:
            Danh sách thông số riêng của tài sản
        """
        response = self._client.table('thongso_taisan') \
            .select('*, thongso:ma_thong_so(ten_thong_so, chi_tiet_thong_so)') \
            .eq('ma_tai_san', asset_id) \
            .execute()
                
        return response.data
    
    def get_asset_group_specifications(self, asset_id):
        """
        Lấy thông số chung của nhóm tài sản
        
        Args:
            asset_id: ID của tài sản
            
        Returns:
            Danh sách thông số chung của nhóm tài sản
        """
        # Lấy thông tin tài sản để biết nhóm tài sản
        asset_response = self._client.table('taisan') \
            .select('*, chitietphieunhap:ma_chi_tiet_pn(ma_nhom_ts)') \
            .eq('ma_tai_san', asset_id) \
            .execute()
            
        if not asset_response.data or len(asset_response.data) == 0:
            return []
        
        asset = asset_response.data[0]
        
        # Kiểm tra nếu có thông tin nhóm tài sản
        if not asset.get('chitietphieunhap') or not asset['chitietphieunhap'].get('ma_nhom_ts'):
            return []
        
        ma_nhom_ts = asset['chitietphieunhap']['ma_nhom_ts']
        
        # Lấy thông số từ bảng ThongSo dựa trên nhóm tài sản
        thongso_response = self._client.table('thongso') \
            .select('*') \
            .eq('ma_nhom_ts', ma_nhom_ts) \
            .execute()
        
        return thongso_response.data
    
    def update_specification(self, asset_id, thongso_id, data):
        """
        Cập nhật hoặc thêm mới thông số kỹ thuật
        
        Args:
            asset_id: ID tài sản
            thongso_id: ID thông số
            data: Dữ liệu cập nhật
            
        Returns:
            Kết quả cập nhật
        """
        # Kiểm tra xem đã tồn tại bản ghi cho thông số này chưa
        check_response = self._client.table('thongso_taisan') \
            .select('ma_thong_so_ts') \
            .eq('ma_tai_san', asset_id) \
            .eq('ma_thong_so', thongso_id) \
            .execute()
        
        if check_response.data and len(check_response.data) > 0:
            # Đã tồn tại, cập nhật
            ma_thong_so_ts = check_response.data[0]['ma_thong_so_ts']
            response = self._client.table('thongso_taisan') \
                .update(data) \
                .eq('ma_thong_so_ts', ma_thong_so_ts) \
                .execute()
        else:
            # Chưa tồn tại, thêm mới
            insert_data = {
                'ma_tai_san': asset_id,
                'ma_thong_so': thongso_id,
                'gia_tri': data.get('gia_tri'),
                'tinh_trang': data.get('tinh_trang'),
                'ngay_cap_nhat': data.get('ngay_cap_nhat')
            }
            response = self._client.table('thongso_taisan') \
                .insert(insert_data) \
                .execute()
        
        return response.data
    
    def get_asset_categories(self):
        """
        Lấy danh sách loại tài sản
        
        Returns:
            Danh sách loại tài sản
        """
        response = self._client.table('loaitaisan') \
            .select('*') \
            .execute()
            
        return response.data
    
    def get_asset_groups(self, category_id=None):
        """
        Lấy danh sách nhóm tài sản
        
        Args:
            category_id: ID loại tài sản (nếu cần lọc)
            
        Returns:
            Danh sách nhóm tài sản
        """
        query = self._client.table('nhomtaisan') \
            .select('*, loaitaisan:ma_loai_ts(ten_loai_ts)')
            
        if category_id:
            query = query.eq('ma_loai_ts', category_id)
            
        response = query.execute()
            
        return response.data
    
    def update_specification_by_id(self, spec_id, data):
        """
        Cập nhật thông số kly thuật theo ID thông số

        Args:
            spec_id: ID thông số cần cập nhật (ma_thong_so_ts)
            data: Dữ liệu cập nhật
        
        returns:
            kết quả cập nhật
        """
        response = self._client.table('thongso_taisan') \
        .update(data) \
        .eq('ma_thong_so_ts', spec_id) \
        .execute()
        
        return response.data
    
    def get_asset_by_seri(self, seri):
        """
        Lấy thông tin tài sản theo số seri
    
        Args:
            seri: Số seri của tài sản
        
        Returns:
            Thông tin tài sản hoặc None nếu không tìm thấy
        """
        response = self._client.table('taisan') \
            .select('*, chitietphieunhap:ma_chi_tiet_pn(ten_tai_san, ma_nhom_ts, nhomtaisan:ma_nhom_ts(ten_nhom_ts, loaitaisan:ma_loai_ts(ten_loai_ts)))') \
            .eq('so_seri', seri) \
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    def get_asset_movement_history(self, asset_id):
        """
        Lấy lịch sử di chuyển của tài sản
    
        Args:
            asset_id: ID của tài sản
        
        Returns:
            Danh sách lịch sử di chuyển
        """
        response = self._client.table('lichsudichuyentaisan') \
            .select('*, phong_cu:ma_phong_cu(ten_phong), phong_moi:ma_phong_moi(ten_phong)') \
            .eq('ma_tai_san', asset_id) \
            .order('ngay_ban_giao', desc=True) \
            .execute()
        
        return response.data
    
    # Thêm hoặc cập nhật phương thức update_asset trong AssetService

    def update_asset(self, asset_id, data):
        """
        Cập nhật thông tin tài sản
        
        Args:
            asset_id: ID tài sản cần cập nhật
            data: Dữ liệu cập nhật (dict)
            
        Returns:
            Kết quả cập nhật
        """
        # Chuẩn hóa dữ liệu trước khi gửi đến supabase
        if 'ngay_su_dung' in data and data['ngay_su_dung']:
            # Đảm bảo ngày được lưu đúng định dạng ISO
            try:
                date_obj = datetime.fromisoformat(data['ngay_su_dung'])
                data['ngay_su_dung'] = date_obj.isoformat()
            except (ValueError, TypeError):
                # Nếu không phải định dạng ISO, giữ nguyên giá trị
                pass
        
        if 'han_bh' in data and data['han_bh']:
            # Đảm bảo ngày được lưu đúng định dạng ISO
            try:
                date_obj = datetime.fromisoformat(data['han_bh'])
                data['han_bh'] = date_obj.isoformat()
            except (ValueError, TypeError):
                # Nếu không phải định dạng ISO, giữ nguyên giá trị
                pass
        
        # Gửi request cập nhật đến Supabase
        response = self._client.table('taisan') \
            .update(data) \
            .eq('ma_tai_san', asset_id) \
            .execute()
        
        return response.data