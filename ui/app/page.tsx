import type { Metadata } from "next";
import { UltraBrainShell } from "./ultra-brain-shell";

export const metadata: Metadata = {
  title: "Ultra Brain v0.986",
  description: "Ultra Brain UI Studio and Official World System",
};

export default function Home() {
  return <UltraBrainShell />;
}
