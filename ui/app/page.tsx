import type { Metadata } from "next";
import { UltraBrainShell } from "./ultra-brain-shell";

export const metadata: Metadata = {
  title: "Ultra Brain v0.92",
  description: "Ultra Brain Official UI Studio and OS Ecosystem world interface",
};

export default function Home() {
  return <UltraBrainShell />;
}
