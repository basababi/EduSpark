import { Features } from "@/components/Features";
import { Footer } from "@/components/Footer";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { Navbar } from "@/components/Navbar";
import { QuizShowcase } from "@/components/QuizShowcase";
import { TutorShowcase } from "@/components/TutorShowcase";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f8fafc]">
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <TutorShowcase />
      <QuizShowcase />
      <Footer />
    </main>
  );
}
