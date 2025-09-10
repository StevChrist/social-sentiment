"use client";

import Link from "next/link";
import Image from "next/image";
import React from "react";

export function Navbar() {
  return (
    <header className="relative z-50" style={{ height: "64px" }}>
      {/* Bar fixed penuh layar */}
      <div
        className="fixed inset-x-0"
        style={{ top: "10px", height: "64px", pointerEvents: "none" }}
      >
        {/* ===== Logo: diposisikan terhadap viewport (bukan container) ===== */}
        <div
          className="absolute"
          style={{
            left: "60px",
            top: "50%",
            transform: "translateY(-50%)",
            pointerEvents: "auto",
          }}
        >
          <Link href="/" className="flex items-center" aria-label="InstaSentiment Home">
            <Image
              src="/Logo PEN White.png"
              alt="InstaSentiment Logo"
              width={50}  // px
              height={50} // px
              priority
            />
          </Link>
        </div>

        {/* ===== Nav container: menu center dengan maxWidth ===== */}
        <nav
          className="relative mx-auto"
          style={{ height: "64px", maxWidth: "1200px" }}
        >
          {/* Menu tengah (pill) */}
          <div
            className="absolute"
            style={{
              left: "50%",
              top: "50%",
              transform: "translate(-50%, -50%)",
              pointerEvents: "auto",
            }}
          >
            <ul
              className="flex items-center backdrop-blur"
              style={{
                gap: "24px",
                padding: "8px 20px",
                borderRadius: "9999px",
                backgroundColor: "rgba(44, 68, 76, 0.6)",
                border: "1px solid rgba(255,255,255,0.1)",
                boxShadow: "0 4px 12px rgba(0,0,0,0.25)",
              }}
            >
              {/* Jika section ada di halaman yang sama, gunakan anchor #how / #try / #contact */}
              <li><Link href="/"         style={linkStyle} className="hover:opacity-100">Home</Link></li>
              <li><Link href="#how"      style={linkStyle} className="hover:opacity-100">How it Works</Link></li>
              <li><Link href="#try"      style={linkStyle} className="hover:opacity-100">Try!</Link></li>
            </ul>
          </div>
        </nav>
      </div>
    </header>
  );
}

const linkStyle: React.CSSProperties = {
  fontSize: "14px",
  fontWeight: 600,
  color: "rgba(245,245,245,0.9)",
};
