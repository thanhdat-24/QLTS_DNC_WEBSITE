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

    def get_active_inventory_checks(self):
        """Lấy danh sách đợt kiểm kê đang diễn ra"""
        response = self.supabase.client.table('dotkiemke') \
            .select('*') \
            .lte('ngay_bat_dau', datetime.now().date().isoformat()) \
            .gte('ngay_ket_thuc', datetime.now().date().isoformat()) \
            .execute()
        return response.data

    def process_inventory_scan(self, inventory_check_id, asset_id, room_id):
        """Xử lý quét QR code trong quá trình kiểm kê"""
        try:
            # Lấy thông tin tài sản
            asset = self.get_asset_detail(asset_id)
            if not asset:
                raise Exception('Không tìm thấy tài sản')
            
            # Kiểm tra xem tài sản đã được kiểm kê trong đợt này chưa
            existing = self.supabase.client.table('kiemketaisan') \
                .select('*') \
                .eq('ma_dot_kiem_ke', inventory_check_id) \
                .eq('ma_tai_san', asset_id) \
                .execute()
            
            if existing.data:
                raise Exception('Tài sản này đã được kiểm kê trong đợt hiện tại')
            
            # Thêm bản ghi kiểm kê
            inventory_data = {
                'ma_dot_kiem_ke': inventory_check_id,
                'ma_tai_san': asset_id,
                'ma_phong': room_id,
                'tinh_trang': asset.get('tinh_trang_sp', 'Chưa xác định'),
                'thoi_gian_kiem': datetime.now().isoformat()
            }
            
            result = self.supabase.client.table('kiemketaisan').insert(inventory_data).execute()
            
            if not result.data:
                raise Exception('Không thể lưu kết quả kiểm kê')
            
            # Trả về thông tin để hiển thị
            return {
                'ma_tai_san': asset_id,
                'ten_tai_san': asset.get('chitietphieunhap', {}).get('ten_tai_san', 'Không xác định'),
                'ten_nhom_ts': asset.get('chitietphieunhap', {}).get('nhomtaisan', {}).get('ten_nhom_ts', 'Không xác định'),
                'thoi_gian_kiem': inventory_data['thoi_gian_kiem'],
                'trang_thai': 'Thành công'
            }
        except Exception as e:
            print(f"Error in process_inventory_scan: {str(e)}")
            raise e

    def _update_group_inventory_count(self, inventory_check_id, group_id, room_id):
        """Cập nhật số lượng kiểm kê cho nhóm tài sản"""
        # Lấy hoặc tạo bản ghi kiểm kê nhóm
        existing = self.supabase.client.table('kiemke_taisanchung') \
            .select('*') \
            .eq('ma_dot_kiem_ke', inventory_check_id) \
            .eq('ma_nhom_ts', group_id) \
            .eq('ma_phong', room_id) \
            .execute()
        
        if existing.data:
            # Cập nhật số lượng
            record = existing.data[0]
            self.supabase.client.table('kiemke_taisanchung') \
                .update({'so_luong_thuc_te': record['so_luong_thuc_te'] + 1}) \
                .eq('ma_kiem_ke_ts_chung', record['ma_kiem_ke_ts_chung']) \
                .execute()
        else:
            # Tạo bản ghi mới
            system_count = self._get_system_asset_count(group_id, room_id)
            self.supabase.client.table('kiemke_taisanchung').insert({
                'ma_dot_kiem_ke': inventory_check_id,
                'ma_nhom_ts': group_id,
                'ma_phong': room_id,
                'so_luong_he_thong': system_count,
                'so_luong_thuc_te': 1
            }).execute()

    def _get_system_asset_count(self, group_id, room_id):
        """Lấy số lượng tài sản theo nhóm trong hệ thống"""
        response = self.supabase.client.table('taisan') \
            .select('ma_tai_san', count='exact') \
            .eq('ma_phong', room_id) \
            .eq('chitietphieunhap.ma_nhom_ts', group_id) \
            .execute()
        return response.count

    def get_inventory_summary(self, inventory_check_id, room_id=None):
        """Lấy tổng hợp kết quả kiểm kê"""
        query = self.supabase.client.table('kiemke_taisanchung') \
            .select('*, nhomtaisan:ma_nhom_ts(ten_nhom_ts)') \
            .eq('ma_dot_kiem_ke', inventory_check_id)
        
        if room_id:
            query = query.eq('ma_phong', room_id)
        
        response = query.execute()
        
        return {
            'groups': [{
                'ten_nhom_ts': item['nhomtaisan']['ten_nhom_ts'],
                'so_luong_he_thong': item['so_luong_he_thong'],
                'so_luong_thuc_te': item['so_luong_thuc_te']
            } for item in response.data]
        }

    def get_rooms(self):
        """
        Lấy danh sách tất cả các phòng
        
        Returns:
            Danh sách phòng với thông tin tòa nhà và tầng
        """
        response = self.supabase.client.table('phong') \
            .select('''
                ma_phong,
                ten_phong,
                suc_chua,
                tang:ma_tang (
                    ten_tang,
                    toanha:ma_toa (
                        ten_toa
                    )
                )
            ''') \
            .execute()
        
        # Xử lý và format dữ liệu trả về
        rooms = []
        for room in response.data:
            # Lấy thông tin tầng và tòa nhà
            tang_info = room.get('tang', {})
            toa_info = tang_info.get('toanha', {}) if tang_info else {}
            
            # Format tên phòng hiển thị
            display_name = f"{toa_info.get('ten_toa', '')} - {tang_info.get('ten_tang', '')} - {room.get('ten_phong', '')}"
            
            rooms.append({
                'ma_phong': room.get('ma_phong'),
                'ten_phong': display_name.strip(' -'),  # Loại bỏ dấu gạch ngang thừa
                'suc_chua': room.get('suc_chua')
            })
        
        return rooms