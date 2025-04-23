from datetime import datetime
from services.supabase_service import SupabaseService

class NotificationService:
    """
    Dịch vụ quản lý thông báo
    """
    def __init__(self):
        self.supabase = SupabaseService()
    
    def get_notifications(self, user_id, limit=10, offset=0, include_read=False, count_only=False):
        """
        Lấy danh sách thông báo của người dùng
        
        Args:
            user_id: ID của tài khoản người dùng
            limit: Số lượng thông báo tối đa cần lấy
            offset: Vị trí bắt đầu lấy
            include_read: Có bao gồm thông báo đã đọc không
            count_only: Chỉ đếm số lượng thông báo
        
        Returns:
            Danh sách thông báo và tổng số thông báo chưa đọc (hoặc tổng số thông báo nếu count_only=True)
        """
        # Tạo query cơ bản
        if count_only:
            # Nếu chỉ cần đếm, không cần lấy dữ liệu
            count_query = self.supabase.client.table('thongbao') \
                .select('ma_thongbao', count='exact') \
                .eq('ma_tk', user_id)
                
            if not include_read:
                count_query = count_query.eq('da_doc', False)
                
            count_response = count_query.execute()
            return count_response.count, 0
        
        # Nếu cần lấy dữ liệu
        query = self.supabase.client.table('thongbao') \
            .select('*') \
            .eq('ma_tk', user_id) \
            .order('ngay_tao', desc=True) \
            .limit(limit) \
            .offset(offset)
        
        # Nếu không bao gồm thông báo đã đọc, thêm điều kiện lọc
        if not include_read:
            query = query.eq('da_doc', False)
        
        # Thực thi query
        response = query.execute()
        
        # Lấy tổng số thông báo chưa đọc
        unread_count_query = self.supabase.client.table('thongbao') \
            .select('ma_thongbao', count='exact') \
            .eq('ma_tk', user_id) \
            .eq('da_doc', False) \
            .execute()
        
        return response.data, unread_count_query.count
    
    def mark_as_read(self, notification_id):
        """
        Đánh dấu thông báo là đã đọc
        
        Args:
            notification_id: ID của thông báo
        
        Returns:
            Kết quả cập nhật
        """
        response = self.supabase.client.table('thongbao') \
            .update({'da_doc': True}) \
            .eq('ma_thongbao', notification_id) \
            .execute()
        
        return response.data
    
    def mark_all_as_read(self, user_id):
        """
        Đánh dấu tất cả thông báo của người dùng là đã đọc
        
        Args:
            user_id: ID của tài khoản người dùng
        
        Returns:
            Kết quả cập nhật
        """
        response = self.supabase.client.table('thongbao') \
            .update({'da_doc': True}) \
            .eq('ma_tk', user_id) \
            .eq('da_doc', False) \
            .execute()
        
        return response.data
    
    def create_notification(self, user_id, type, message, reference_type=None, reference_id=None, link=None):
        """
        Tạo thông báo mới
    
        Args:
            user_id: ID tài khoản nhận thông báo
            type: Loại thông báo ('info', 'update', 'warning', 'error')
            message: Nội dung thông báo
            reference_type: Loại đối tượng tham chiếu ('taisan', 'thongso', v.v.)
            reference_id: ID của đối tượng tham chiếu
            link: Đường dẫn đến trang chi tiết
    
        Returns:
            Thông báo đã được tạo
        """
        notification_data = {
            'ma_tk': user_id,
            'loai_thongbao': type,
            'noi_dung': message,
            'da_doc': False,
            'ngay_tao': datetime.now().isoformat()
        }
    
        # Thêm các thông tin tùy chọn nếu có
        if reference_type:
            notification_data['doi_tuong_tham_chieu'] = reference_type
    
        if reference_id:
            notification_data['ma_tham_chieu'] = reference_id
    
        if link:
            notification_data['lien_ket'] = link
    
        # Thêm vào database
        response = self.supabase.client.table('thongbao') \
            .insert(notification_data) \
            .execute()
    
        return response.data
    
    def get_notification_by_id(self, notification_id):
        """
        Lấy thông tin chi tiết của thông báo
        
        Args:
            notification_id: ID của thông báo
        
        Returns:
            Thông tin thông báo
        """
        response = self.supabase.client.table('thongbao') \
            .select('*') \
            .eq('ma_thongbao', notification_id) \
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    def delete_notification(self, notification_id):
        """
        Xóa thông báo
        
        Args:
            notification_id: ID của thông báo
        
        Returns:
            Kết quả xóa
        """
        response = self.supabase.client.table('thongbao') \
            .delete() \
            .eq('ma_thongbao', notification_id) \
            .execute()
        
        return response.data
    
    def delete_old_notifications(self, days=30):
        """
        Xóa các thông báo cũ hơn số ngày quy định
        
        Args:
            days: Số ngày giữ lại thông báo
        
        Returns:
            Kết quả xóa
        """
        # Tính toán ngày cần xóa
        cutoff_date = (datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        # Xóa thông báo
        response = self.supabase.client.table('thongbao') \
            .delete() \
            .lt('ngay_tao', cutoff_date) \
            .execute()
        
        return response.data