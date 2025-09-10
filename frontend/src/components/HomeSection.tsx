"use client";

export default function HomeSection() {
  return (
    <section
      style={{
        minHeight: "calc(100vh - 74px)", // full height minus navbar
        display: "flex",
        alignItems: "center", // vertikal center
        justifyContent: "center", // horizontal center
        textAlign: "center",
        boxSizing: "border-box",
      }}
    >
      <div>
        <h1
          style={{
            fontSize: "60px",
            fontWeight: 600,
            color: "#F5F5F5",
            margin: 0,
          }}
        >
          <span style={{ color: "rgba(245,245,245,0.8)" }}>Welcome To</span>{" "}
          Social<span style={{ color: "#A8C4EC" }}>Sentiment</span>
        </h1>

        <p
          style={{
            marginTop: "8px",
            fontSize: "18px",
            color: "rgba(245,245,245,0.8)",
          }}
        >
          Hi, do you want to try to analyst your content?
        </p>

        <div style={{ marginTop: "24px" }}>
          <a href="#try" className="btn-gradient">
            Let&apos;s Go
          </a>
        </div>
      </div>
    </section>
  );
}
