/**
 * api.ts - Helper hỗ trợ gọi API tự động đính kèm Access Token 
 * và xử lý cơ chế làm mới Token (Refresh Token) tự động khi gặp lỗi 401.
 */

export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const isClient = typeof window !== "undefined";
  let token = isClient ? localStorage.getItem("access_token") : null;

  // Clone lại options để tránh sửa đổi tham chiếu gốc
  const newOptions = { ...options };
  
  // Thiết lập Headers mặc định
  const headers = new Headers(newOptions.headers || {});
  
  // Tự động đính kèm Authorization header nếu có Access Token
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  newOptions.headers = headers;

  // Thực hiện request đầu tiên
  let response = await fetch(url, newOptions);

  // Nếu gặp lỗi 401 (Token hết hạn hoặc không hợp lệ)
  if (response.status === 401) {
    const refreshToken = isClient ? localStorage.getItem("refresh_token") : null;

    if (refreshToken) {
      try {
        // Tự động gọi API refresh token
        const refreshResponse = await fetch("http://localhost:8000/api/auth/refresh", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        const refreshData = await refreshResponse.json();

        if (refreshResponse.ok && refreshData.success) {
          // Lưu cặp token mới vào localStorage
          const { access_token, refresh_token: newRefreshToken } = refreshData.data;
          if (isClient) {
            localStorage.setItem("access_token", access_token);
            localStorage.setItem("refresh_token", newRefreshToken);
          }

          // Cập nhật header Authorization với Access Token mới
          const retryHeaders = new Headers(newOptions.headers || {});
          retryHeaders.set("Authorization", `Bearer ${access_token}`);
          newOptions.headers = retryHeaders;

          // Thực hiện lại (retry) request ban đầu với token mới
          response = await fetch(url, newOptions);
        } else {
          // Refresh token cũng hết hạn -> Thực hiện đăng xuất
          handleTokenExpired();
        }
      } catch (err) {
        handleTokenExpired();
      }
    } else {
      // Không tìm thấy refresh token để làm mới -> Đăng xuất
      handleTokenExpired();
    }
  }

  return response;
}

function handleTokenExpired() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("username");
    alert("Phiên đăng nhập của bạn đã hết hạn, vui lòng đăng nhập lại.");
    window.location.href = "/";
  }
}
