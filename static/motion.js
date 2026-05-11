(function () {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    document.documentElement.classList.add("motion-ready");

    if (reducedMotion) {
        document.querySelectorAll("[data-count]").forEach((item) => {
            item.textContent = `${item.dataset.prefix || ""}${item.dataset.count || "0"}${item.dataset.suffix || ""}`;
        });
        return;
    }

    // =====================
    // 1. SCROLL REVEAL
    // =====================
    const revealItems = document.querySelectorAll(
        ".auth-hero, .auth-card, .dashboard-nav, .hero-panel, .assistant-panel, .details-panel, .metric-card, .form-panel, .chart-panel, .table-panel, .leaderboard-hero, .podium-card, .admin-hero-panel, .stat-card, .glass-card"
    );

    revealItems.forEach((item, index) => {
        item.style.setProperty("--motion-delay", `${Math.min(index * 45, 360)}ms`);
        item.classList.add("motion-reveal");
    });

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    revealItems.forEach((item) => revealObserver.observe(item));

    // =====================
    // 2. COUNT-UP ANIMATION
    // =====================
    function formatValue(value, decimals) {
        return Number(value).toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    const counters = document.querySelectorAll("[data-count]");
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting || entry.target.dataset.animated === "true") return;

            const item = entry.target;
            const rawTarget = item.dataset.count || "0";
            const target = Number(rawTarget);
            const inferredDecimals = rawTarget.includes(".") ? rawTarget.split(".")[1].length : 0;
            const decimals = item.dataset.decimals ? Number(item.dataset.decimals) : inferredDecimals;
            const prefix = item.dataset.prefix || "";
            const suffix = item.dataset.suffix || "";
            const startTime = performance.now();
            const duration = 950;

            item.dataset.animated = "true";

            function tick(now) {
                const elapsed = Math.min((now - startTime) / duration, 1);
                const eased = 1 - Math.pow(1 - elapsed, 3);
                item.textContent = `${prefix}${formatValue(target * eased, decimals)}${suffix}`;
                if (elapsed < 1) {
                    requestAnimationFrame(tick);
                } else {
                    item.textContent = `${prefix}${formatValue(target, decimals)}${suffix}`;
                }
            }

            requestAnimationFrame(tick);
            counterObserver.unobserve(item);
        });
    }, { threshold: 0.45 });

    counters.forEach((item) => counterObserver.observe(item));

    // =====================
    // 3. TABLE ROW STAGGER
    // =====================
    document.querySelectorAll("tbody tr").forEach((row, i) => {
        row.style.opacity = "0";
        row.style.transform = "translateY(10px)";
        row.style.transition = `opacity 0.35s ease ${i * 50}ms, transform 0.35s ease ${i * 50}ms`;
        setTimeout(() => {
            row.style.opacity = "1";
            row.style.transform = "translateY(0)";
        }, 100 + i * 50);
    });

    // =====================
    // 4. BUTTON RIPPLE
    // =====================
    document.addEventListener("click", (e) => {
        const btn = e.target.closest("button, .primary-action, .nav-link, .voice-btn, .pdf-btn, .oauth-btn");
        if (!btn) return;

        const ripple = document.createElement("span");
        const rect = btn.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);

        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${e.clientX - rect.left - size / 2}px;
            top: ${e.clientY - rect.top - size / 2}px;
            background: rgba(255,255,255,0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: rippleAnim 0.5s ease-out forwards;
            pointer-events: none;
            z-index: 10;
        `;

        btn.style.position = "relative";
        btn.style.overflow = "hidden";
        btn.appendChild(ripple);
        setTimeout(() => ripple.remove(), 500);
    });

    // =====================
    // 5. INPUT FOCUS SCALE
    // =====================
    document.querySelectorAll("input, textarea").forEach(input => {
        input.addEventListener("focus", () => {
            input.style.transform = "scale(1.01)";
        });
        input.addEventListener("blur", () => {
            input.style.transform = "scale(1)";
        });
    });

    // =====================
    // 6. NAVBAR SCROLL SHADOW
    // =====================
    const nav = document.querySelector(".dashboard-nav");
    if (nav) {
        window.addEventListener("scroll", () => {
            nav.style.boxShadow = window.scrollY > 10
                ? "0 8px 32px rgba(15,23,42,0.15)"
                : "";
        }, { passive: true });
    }

    // =====================
    // 7. PROGRESS BARS
    // =====================
    document.querySelectorAll(".progress-track span").forEach(bar => {
        const width = bar.style.width;
        bar.style.width = "0%";
        setTimeout(() => {
            bar.style.transition = "width 1s cubic-bezier(0.16, 1, 0.3, 1)";
            bar.style.width = width;
        }, 400);
    });

    // =====================
    // 8. PAGE FADE IN
    // =====================
    document.documentElement.style.opacity = "0";
    document.documentElement.style.transition = "opacity 0.4s ease";
    window.addEventListener("load", () => {
        document.documentElement.style.opacity = "1";
    });

    // =====================
    // 9. INJECT KEYFRAMES
    // =====================
    const style = document.createElement("style");
    style.textContent = `
        @keyframes rippleAnim {
            to { transform: scale(2.5); opacity: 0; }
        }
        .motion-reveal {
            opacity: 0;
            transform: translateY(18px);
            transition: opacity 0.55s ease var(--motion-delay, 0ms),
                        transform 0.55s ease var(--motion-delay, 0ms);
        }
        .motion-reveal.is-visible {
            opacity: 1;
            transform: translateY(0);
        }
    `;
    document.head.appendChild(style);

})();