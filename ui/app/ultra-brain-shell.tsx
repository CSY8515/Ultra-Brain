"use client";

import { useEffect, useState } from "react";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";

const OS_ECOSYSTEM_URL = "https://8javbq85jtappi6tkdhkt7g.streamlit.app/";

export function UltraBrainShell() {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const image = document.querySelector<HTMLImageElement>(".world-art");
    if (image?.complete && image.naturalWidth > 0) setLoaded(true);
  }, []);

  return (
    <main className="world-shell" aria-label="Ultra Brain">
      {!loaded && (
        <div className="world-loading" aria-live="polite">
          <div className="loading-mark" />
          <p>Ultra Brain을 여는 중</p>
          <Skeleton baseColor="#081111" highlightColor="#17251f" height={2} width={180} />
        </div>
      )}

      <img
        className={`world-art ${loaded ? "is-loaded" : ""}`}
        src="/ultra-brain-world.png"
        alt="중앙 태양 구체를 품은 세계수와 하단의 OS Ecosystem 구체"
        onLoad={() => setLoaded(true)}
      />
      <div className="world-vignette" aria-hidden="true" />

      <section id="ultra-brain" className="world-center" aria-labelledby="ultra-brain-title">
        <span className="title-rule title-rule-top" aria-hidden="true" />
        <h1 id="ultra-brain-title">Ultra Brain</h1>
        <span className="title-rule" aria-hidden="true" />
      </section>

      <a
        className="ecosystem-seed"
        href={OS_ECOSYSTEM_URL}
        target="_blank"
        rel="noreferrer"
        aria-label="OS Ecosystem 열기, 새 창"
      >
        <span className="seed-aura" aria-hidden="true" />
        <span className="seed-copy">
          <strong>OS Ecosystem</strong>
          <span className="seed-action">진입 <b>↗</b></span>
        </span>
      </a>

      <img
        className="world-focus-art"
        src="/ultra-brain-world.png"
        alt=""
        aria-hidden="true"
      />
    </main>
  );
}
