/**
 * API Client - Hệ thống quản lý tài sản
 * Cung cấp các function gọi API đến backend
 */

class AssetManagerApi {
    /**
     * Khởi tạo API client
     */
    constructor() {
        this.baseUrl = '';  // Nếu API và frontend cùng domain, để trống
    }

    /**
     * Lấy danh sách tài sản
     * @param {Object} params - Các tham số truy vấn
     * @returns {Promise} - Promise trả về dữ liệu
     */
    async getAssets(params = {}) {
        // Tạo query string từ params
        const queryParams = new URLSearchParams();
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== null) {
                queryParams.append(key, params[key]);
            }
        });
        
        const url = `${this.baseUrl}/api/assets?${queryParams.toString()}`;
        
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Lỗi HTTP: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Lỗi khi lấy danh sách tài sản:', error);
            throw error;
        }
    }

    /**
     * Lấy chi tiết tài sản
     * @param {number} assetId - ID của tài sản
     * @returns {Promise} - Promise trả về dữ liệu
     */
    async getAssetDetail(assetId) {
        const url = `${this.baseUrl}/api/assets/${assetId}`;
        
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Lỗi HTTP: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Lỗi khi lấy chi tiết tài sản:', error);
            throw error;
        }
    }

    /**
     * Cập nhật thông số kỹ thuật
     * @param {number} specId - ID của thông số
     * @param {Object} data - Dữ liệu cập nhật
     * @returns {Promise} - Promise trả về kết quả
     */
    async updateSpecification(specId, data) {
        const url = `${this.baseUrl}/api/specifications/${specId}`;
        
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            
            if (!response.ok) {
                throw new Error(`Lỗi HTTP: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Lỗi khi cập nhật thông số:', error);
            throw error;
        }
    }

    /**
     * Lấy danh sách loại tài sản
     * @returns {Promise} - Promise trả về dữ liệu
     */
    async getCategories() {
        const url = `${this.baseUrl}/api/categories`;
        
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Lỗi HTTP: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Lỗi khi lấy danh sách loại tài sản:', error);
            throw error;
        }
    }

    /**
     * Lấy danh sách nhóm tài sản
     * @param {number} categoryId - ID loại tài sản (optional)
     * @returns {Promise} - Promise trả về dữ liệu
     */
    async getGroups(categoryId) {
        let url = `${this.baseUrl}/api/groups`;
        if (categoryId) {
            url += `?category_id=${categoryId}`;
        }
        
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Lỗi HTTP: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Lỗi khi lấy danh sách nhóm tài sản:', error);
            throw error;
        }
    }
}

// Khởi tạo instance để sử dụng trong ứng dụng
const apiClient = new AssetManagerApi();