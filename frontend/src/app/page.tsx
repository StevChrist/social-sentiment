import { Navbar } from "@/components/Navbar";
import HomeSection from "@/components/HomeSection";
import HowSection from "@/components/HowSection";
import TrySection from "@/components/TrySection";

export default function HomePage() {
  return (
    <main style={{ minHeight: "100vh" }}>
      <Navbar />
      <HomeSection />
      <HowSection />
      <TrySection />
    </main>
  );
}
