"use client";

import React, { useState } from "react";
import Image from "next/image";

export default function Home() {
  // Trạng thái chung
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isRegister, setIsRegister] = useState(false);

  // Trạng thái cho form Đăng nhập
  const [identity, setIdentity] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  // Trạng thái cho form Đăng ký
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Trạng thái mật khẩu chung
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    if (isRegister) {
      // --- XỬ LÝ ĐĂNG KÝ ---
      if (!username.trim()) {
        setError("Vui lòng nhập tên đăng nhập.");
        return;
      }
      if (username.trim().length < 3) {
        setError("Tên đăng nhập phải chứa ít nhất 3 ký tự.");
        return;
      }
      if (!/^[a-zA-Z0-9_-]+$/.test(username.trim())) {
        setError("Tên đăng nhập chỉ được chứa chữ cái, số, dấu gạch dưới và gạch ngang.");
        return;
      }
      if (!email.trim()) {
        setError("Vui lòng nhập email.");
        return;
      }
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailRegex.test(email.trim())) {
        setError("Email không hợp lệ.");
        return;
      }
      if (!password) {
        setError("Vui lòng nhập mật khẩu.");
        return;
      }
      if (password.length < 6) {
        setError("Mật khẩu phải chứa ít nhất 6 ký tự.");
        return;
      }
      if (password !== confirmPassword) {
        setError("Mật khẩu xác nhận không khớp.");
        return;
      }

      setIsLoading(true);

      try {
        const response = await fetch("http://localhost:8000/api/auth/register", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username: username.trim().toLowerCase(),
            email: email.trim().toLowerCase(),
            password: password,
          }),
        });

        const resData = await response.json();

        if (!response.ok || !resData.success) {
          throw new Error(resData.message || "Đăng ký không thành công. Vui lòng thử lại.");
        }

        setSuccessMessage("Đăng ký tài khoản thành công! Đang chuyển sang trang đăng nhập...");
        
        // Chuyển sang form đăng nhập sau 2 giây và điền sẵn tên đăng nhập vừa tạo
        setTimeout(() => {
          setIdentity(username.trim().toLowerCase());
          setIsRegister(false);
          setSuccessMessage("");
          setPassword("");
          setConfirmPassword("");
        }, 2000);
      } catch (err: any) {
        setError(err.message || "Không thể kết nối đến máy chủ API.");
      } finally {
        setIsLoading(false);
      }
    } else {
      // --- XỬ LÝ ĐĂNG NHẬP ---
      if (!identity.trim()) {
        setError("Vui lòng nhập tên đăng nhập hoặc email.");
        return;
      }
      if (!password) {
        setError("Vui lòng nhập mật khẩu.");
        return;
      }
      if (password.length < 6) {
        setError("Mật khẩu phải chứa ít nhất 6 ký tự.");
        return;
      }

      setIsLoading(true);

      try {
        const response = await fetch("http://localhost:8000/api/auth/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            identity: identity.trim(),
            password: password,
          }),
        });

        const resData = await response.json();

        if (!response.ok || !resData.success) {
          throw new Error(resData.message || "Tên đăng nhập hoặc mật khẩu không chính xác.");
        }

        // Lưu JWT Token và thông tin user vào localStorage
        const { access_token, refresh_token } = resData.data;
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("refresh_token", refresh_token);
        
        const displayUsername = identity.includes("@") ? identity.split("@")[0] : identity;
        localStorage.setItem("username", displayUsername);

        setIsSuccess(true);
        
        // Chuyển hướng sang trang chat sau 1 giây
        setTimeout(() => {
          window.location.href = "/chat";
        }, 1000);
      } catch (err: any) {
        setError(err.message || "Không thể kết nối đến máy chủ API.");
      } finally {
        setIsLoading(false);
      }
    }
  };

  const toggleMode = () => {
    setIsRegister(!isRegister);
    setError("");
    setSuccessMessage("");
    setPassword("");
    setConfirmPassword("");
  };

  return (
    <div className="login-container">
      {/* Khối cầu mờ nền chuyển động */}
      <div className="bg-container">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>

      <div className="login-card">
        {/* Tiêu đề & Logo thương hiệu */}
        <div className="brand">
          <div className="logo-wrapper">
            <div className="logo-inner">
              <Image
                src="/logo.jpg"
                alt="RAG Lawyer Logo"
                width={86}
                height={86}
                className="logo-image"
                priority
              />
            </div>
          </div>
          <h1>{isRegister ? "TẠO TÀI KHOẢN" : "RAG LAWYER"}</h1>
          <p>{isRegister ? "Đăng ký Trợ lý Pháp lý AI" : "Trợ lý Pháp lý AI Tự trị"}</p>
        </div>

        {/* Trạng thái thành công đăng nhập hoặc Biểu mẫu */}
        {isSuccess ? (
          <div style={{ textAlign: "center", padding: "20px 0" }}>
            <div style={{ 
              width: "64px", 
              height: "64px", 
              borderRadius: "50%", 
              background: "rgba(16, 185, 129, 0.1)", 
              border: "2px solid var(--success)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 24px",
              color: "var(--success)"
            }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>
            <h2 style={{ fontSize: "20px", fontWeight: "700", marginBottom: "8px" }}>Đăng nhập thành công!</h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px" }}>Đang kết nối hệ thống trợ lý ảo...</p>
            <div className="btn-submit" style={{ cursor: "default", opacity: 0.8 }}>
              Đang chuyển hướng...
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate>
            {error && (
              <div className="error-banner">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <span>{error}</span>
              </div>
            )}

            {successMessage && (
              <div className="success-banner" style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                background: "rgba(16, 185, 129, 0.1)",
                border: "1px solid var(--success)",
                borderRadius: "12px",
                padding: "12px 16px",
                marginBottom: "20px",
                color: "var(--success)",
                fontSize: "14px",
                lineHeight: "1.5"
              }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>{successMessage}</span>
              </div>
            )}

            {isRegister ? (
              <>
                {/* Trường Tên đăng nhập (Chỉ đăng ký) */}
                <div className="form-group">
                  <label className="form-label" htmlFor="username">Tên đăng nhập</label>
                  <div className="input-wrapper">
                    <input
                      type="text"
                      id="username"
                      className="form-input"
                      placeholder="Nhập tên đăng nhập..."
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      disabled={isLoading}
                      required
                    />
                    <span className="input-icon">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                      </svg>
                    </span>
                  </div>
                </div>

                {/* Trường Email (Chỉ đăng ký) */}
                <div className="form-group">
                  <label className="form-label" htmlFor="email">Email</label>
                  <div className="input-wrapper">
                    <input
                      type="email"
                      id="email"
                      className="form-input"
                      placeholder="Nhập địa chỉ email..."
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={isLoading}
                      required
                    />
                    <span className="input-icon">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                        <polyline points="22,6 12,13 2,6"></polyline>
                      </svg>
                    </span>
                  </div>
                </div>
              </>
            ) : (
              /* Trường Tên đăng nhập hoặc Email (Chỉ đăng nhập) */
              <div className="form-group">
                <label className="form-label" htmlFor="identity">Tên đăng nhập hoặc Email</label>
                <div className="input-wrapper">
                  <input
                    type="text"
                    id="identity"
                    className="form-input"
                    placeholder="Tên đăng nhập hoặc email..."
                    value={identity}
                    onChange={(e) => setIdentity(e.target.value)}
                    disabled={isLoading}
                    required
                  />
                  <span className="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                      <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                  </span>
                </div>
              </div>
            )}

            {/* Trường Mật khẩu (Cả hai chế độ) */}
            <div className="form-group">
              <label className="form-label" htmlFor="password">Mật khẩu</label>
              <div className="input-wrapper">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  required
                />
                <span className="input-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                  </svg>
                </span>
                <button
                  type="button"
                  style={{
                    position: "absolute",
                    right: "16px",
                    background: "none",
                    border: "none",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "0"
                  }}
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading}
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                      <line x1="1" y1="1" x2="23" y2="23"></line>
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Trường Xác nhận mật khẩu (Chỉ đăng ký) */}
            {isRegister && (
              <div className="form-group">
                <label className="form-label" htmlFor="confirmPassword">Xác nhận mật khẩu</label>
                <div className="input-wrapper">
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    id="confirmPassword"
                    className="form-input"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    disabled={isLoading}
                    required
                  />
                  <span className="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                      <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    </svg>
                  </span>
                  <button
                    type="button"
                    style={{
                      position: "absolute",
                      right: "16px",
                      background: "none",
                      border: "none",
                      color: "var(--text-muted)",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      padding: "0"
                    }}
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    disabled={isLoading}
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                        <line x1="1" y1="1" x2="23" y2="23"></line>
                      </svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Các tuỳ chọn Ghi nhớ / Quên mật khẩu (Chỉ đăng nhập) */}
            {!isRegister && (
              <div className="form-actions">
                <label className="remember-me">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    disabled={isLoading}
                  />
                  <span>Ghi nhớ đăng nhập</span>
                </label>
                <a href="#" className="forgot-password" onClick={(e) => { e.preventDefault(); alert("Chức năng khôi phục mật khẩu đang được phát triển."); }}>
                  Quên mật khẩu?
                </a>
              </div>
            )}

            {/* Nút Submit */}
            <button type="submit" className="btn-submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <svg className="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
                    <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.2)"></circle>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor"></path>
                  </svg>
                  <span>Đang xử lý...</span>
                </>
              ) : (
                <>
                  <span>{isRegister ? "Đăng Ký" : "Đăng Nhập"}</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                  </svg>
                </>
              )}
            </button>

            {/* Footer chuyển mode */}
            <div className="form-footer">
              {isRegister ? (
                <>
                  Đã có tài khoản?{" "}
                  <a href="#" onClick={(e) => { e.preventDefault(); toggleMode(); }}>
                    Đăng nhập ngay
                  </a>
                </>
              ) : (
                <>
                  Chưa có tài khoản?{" "}
                  <a href="#" onClick={(e) => { e.preventDefault(); toggleMode(); }}>
                    Đăng ký ngay
                  </a>
                </>
              )}
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

