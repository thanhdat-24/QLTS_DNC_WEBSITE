from datetime import datetime
from services.supabase_service import SupabaseService

def format_currency(value):
    """
    Định dạng số thành tiền VNĐ
    """
    try:
        # Chuyển đổi value thành số dù nó ở dạng nào
        if isinstance(value, str):
            # Loại bỏ tất cả các dấu phân cách và đơn vị
            cleaned_value = value.replace('.', '').replace(',', '').replace(' ', '').replace('VNĐ', '')
            num_value = float(cleaned_value)
        else:
            num_value = float(value)
            
        # Định dạng với dấu chấm ngăn cách hàng nghìn (định dạng Việt Nam)
        formatted = "{:,.0f}".format(num_value).replace(',', '.')
        return f"{formatted} VNĐ"
    except (ValueError, TypeError, AttributeError):
        # Nếu không phải số, trả về giá trị gốc
        return value
        
class AssetService:
    """
    Dịch vụ quản lý tài sản
    """
    def __init__(self):
        self.supabase = SupabaseService()
    
    def get_assets(self, page=1, limit=10, search=None, group=None, status=None):
        """
        Lấy danh sách tài sản với phân trang và lọc
        
        Args:
            page: Trang hiện tại
            limit: Số lượng mỗi trang
            search: Từ khóa tìm kiếm
            group: Lọc theo nhóm tài sản
            status: Lọc theo tình trạng
            
        Returns:
            Danh sách tài sản và thông tin phân trang
        """
        assets, total = self.supabase.get_assets(page, limit, search, group, status)
        
        # Xử lý và chuẩn hóa dữ liệu nếu cần thiết
        for asset in assets:
            # Định dạng ngày tháng để hiển thị
            if asset.get('ngay_su_dung'):
                try:
                    asset['ngay_su_dung_fmt'] = datetime.fromisoformat(asset['ngay_su_dung']).strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    asset['ngay_su_dung_fmt'] = asset['ngay_su_dung']
            
            if asset.get('han_bh'):
                try:
                    asset['han_bh_fmt'] = datetime.fromisoformat(asset['han_bh']).strftime('%d/%m/%Y')
                    # Kiểm tra tình trạng bảo hành
                    asset['con_bao_hanh'] = datetime.fromisoformat(asset['han_bh']) > datetime.now()
                except (ValueError, TypeError):
                    asset['han_bh_fmt'] = asset['han_bh']
                    asset['con_bao_hanh'] = False
        
        # Tính toán thông tin phân trang
        total_pages = max(1, (total + limit - 1) // limit)
        pagination = {
            'page': page,
            'total': total,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'limit': limit
        }
        
        return assets, pagination
    
    def get_asset_detail(self, asset_id):
        """
        Lấy thông tin chi tiết của tài sản
        
        Args:
            asset_id: ID tài sản
            
        Returns:
            Thông tin tài sản
        """
        asset = self.supabase.get_asset_by_id(asset_id)
        
        if not asset:
            return None
        
        # Xử lý dữ liệu nếu cần
        if asset.get('ngay_su_dung'):
            try:
                asset['ngay_su_dung_fmt'] = datetime.fromisoformat(asset['ngay_su_dung']).strftime('%d/%m/%Y')
            except (ValueError, TypeError):
                asset['ngay_su_dung_fmt'] = asset['ngay_su_dung']
                
        if asset.get('han_bh'):
            try:
                asset['han_bh_fmt'] = datetime.fromisoformat(asset['han_bh']).strftime('%d/%m/%Y')
                asset['con_bao_hanh'] = datetime.fromisoformat(asset['han_bh']) > datetime.now()
            except (ValueError, TypeError):
                asset['han_bh_fmt'] = asset['han_bh']
                asset['con_bao_hanh'] = False
        
        return asset
    
    def get_asset_specifications(self, asset_id):
        """
        Lấy cả thông số chung và thông số riêng của tài sản
        
        Args:
            asset_id: ID tài sản
            
        Returns:
            Thông số chung và thông số riêng
        """
        # Lấy thông số chung của nhóm tài sản
        group_specs = self.supabase.get_asset_group_specifications(asset_id)
        
        # Lấy thông số riêng của tài sản
        specific_specs = self.supabase.get_asset_specific_specifications(asset_id)
        
        # Xử lý thông tin ngày cập nhật cho thông số riêng
        for spec in specific_specs:
            if spec.get('ngay_cap_nhat'):
                try:
                    spec['ngay_cap_nhat_fmt'] = datetime.fromisoformat(spec['ngay_cap_nhat']).strftime('%d/%m/%Y %H:%M')
                except (ValueError, TypeError):
                    spec['ngay_cap_nhat_fmt'] = spec['ngay_cap_nhat']
            
            # Kiểm tra có phải thông số tiền tệ không
            is_currency = False
            if spec.get('thongso') and spec['thongso'].get('ten_thong_so'):
                ten_thong_so = spec['thongso'].get('ten_thong_so', '').lower()
                if ('giá' in ten_thong_so or 'tiền' in ten_thong_so or 
                    'chi phí' in ten_thong_so or 'phí' in ten_thong_so or
                    'ngân sách' in ten_thong_so or 'đồng' in ten_thong_so):
                    is_currency = True
            
            # Định dạng giá trị thành tiền VNĐ nếu thông số là giá trị tiền tệ
            if is_currency:
                spec['gia_tri_fmt'] = format_currency(spec['gia_tri'])
            else:
                spec['gia_tri_fmt'] = spec['gia_tri']
        
        return group_specs, specific_specs
    
    def update_specification(self, spec_id, value, status):
        """
        Cập nhật thông số kỹ thuật theo ID của thông số
        
        Args:
            spec_id: ID của bản ghi thông số (ma_thong_so_ts)
            value: Giá trị mới
            status: Tình trạng mới
            
        Returns:
            Kết quả cập nhật
        """
        data = {
            'gia_tri': value,
            'tinh_trang': status,
            'ngay_cap_nhat': datetime.now().isoformat()
        }
        
        return self.supabase.update_specification_by_id(spec_id, data)
    
    def add_specification(self, asset_id, thongso_id, value, status):
        """
        Thêm mới hoặc cập nhật thông số kỹ thuật
        
        Args:
            asset_id: ID tài sản
            thongso_id: ID thông số
            value: Giá trị
            status: Tình trạng
            
        Returns:
            Kết quả thêm/cập nhật
        """
        data = {
            'gia_tri': value,
            'tinh_trang': status,
            'ngay_cap_nhat': datetime.now().isoformat()
        }
        
        return self.supabase.update_specification(asset_id, thongso_id, data)
    
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
        
        # Gọi phương thức update_asset từ SupabaseService
        result = self.supabase.update_asset(asset_id, data)
        
        return result
    
    def get_categories(self):
        """
        Lấy danh sách loại tài sản
        
        Returns:
            Danh sách loại tài sản
        """
        return self.supabase.get_asset_categories()
    
    def get_groups(self, category_id=None):
        """
        Lấy danh sách nhóm tài sản
        
        Args:
            category_id: ID loại tài sản (nếu muốn lọc)
            
        Returns:
            Danh sách nhóm tài sản
        """
        return self.supabase.get_asset_groups(category_id)
    
    def get_asset_by_seri(self, seri):
        """
        Lấy thông tin tài sản theo số seri
    
        Args:
            seri: Số seri của tài sản
        
        Returns:
            Thông tin tài sản hoặc None nếu không tìm thấy
        """
        return self.supabase.get_asset_by_seri(seri)

    def get_asset_stats(self):
        """
        Lấy thống kê tài sản
        
        Returns:
            Thống kê tài sản
        """
        # Trong thực tế, bạn sẽ cần viết query thống kê từ database
        # Đây chỉ là dữ liệu mẫu, bạn cần thay thế bằng dữ liệu thực từ Supabase
        stats = {
            'it': {
                'count': 30,
                'title': 'Thiết bị IT',
                'icon': 'desktop'
            },
            'office': {
                'count': 20,
                'title': 'Thiết bị VP',
                'icon': 'print'
            },
            'furniture': {
                'count': 25,
                'title': 'Nội thất trường học',
                'icon': 'couch'
            },
            'maintenance': {
                'count': 2,
                'title': 'Cần bảo trì',
                'icon': 'exclamation-triangle'
            }
        }
        
        return stats
    
    def get_specification_by_id(self, spec_id):
        """
        Lấy thông tin chi tiết của thông số kỹ thuật theo ID
    
        Args:
            spec_id: ID của thông số
        
        Returns:
            Thông tin thông số hoặc None nếu không tìm thấy
        """
        # Gọi đến Supabase để lấy thông tin thông số
        response = self.supabase.client.table('thongso_taisan') \
            .select('*, thongso:ma_thong_so(ten_thong_so, chi_tiet_thong_so)') \
            .eq('ma_thong_so_ts', spec_id) \
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    def get_thongso_by_id(self, thongso_id):
        """
        Lấy thông tin của thông số theo ID
    
        Args:
            thongso_id: ID của thông số
        
        Returns:
            Thông tin thông số hoặc None nếu không tìm thấy
        """
        response = self.supabase.client.table('thongso') \
            .select('*') \
            .eq('ma_thong_so', thongso_id) \
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None