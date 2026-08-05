import type { Metadata } from "next";
import { UltraBrainShell } from "./ultra-brain-shell";

export const metadata: Metadata = {
  title: "Ultra Brain",
  description: "Ultra Brain과 OS Ecosystem 진입 화면",
};

export default function Home() {
  return <UltraBrainShell />;
}
