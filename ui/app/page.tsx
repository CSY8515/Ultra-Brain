import type { Metadata } from "next";
import { UltraBrainShell } from "./ultra-brain-shell";

export const metadata: Metadata = {
  title: "Ultra Brain v0.96",
  description: "Ultra Brain Advanced Theme and Visual World Engine",
};

export default function Home() {
  return <UltraBrainShell />;
}
