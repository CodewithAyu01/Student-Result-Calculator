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

    // =====================
    // 10. BACKGROUND ANIMATION
    // =====================
    const canvas = document.createElement("canvas");
    canvas.style.cssText = `
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        pointer-events: none;
        z-index: 0;
        opacity: 0.45;
    `;
    document.body.prepend(canvas);

    document.body.style.position = "relative";
    document.querySelectorAll("body > *:not(canvas)").forEach(el => {
        el.style.position = "relative";
        el.style.zIndex = "1";
    });

    const ctx2 = canvas.getContext("2d");

    function resizeCanvas() {
        canvas.width  = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas, { passive: true });

    const orbs = Array.from({ length: 12 }, () => ({
        x:     Math.random() * window.innerWidth,
        y:     Math.random() * window.innerHeight,
        r:     60 + Math.random() * 120,
        dx:    (Math.random() - 0.5) * 0.4,
        dy:    (Math.random() - 0.5) * 0.4,
        color: Math.random() > 0.5 ? "37,99,235" : "15,159,110",
        alpha: 0.04 + Math.random() * 0.08
    }));

    function drawOrbs() {
        ctx2.clearRect(0, 0, canvas.width, canvas.height);

        orbs.forEach(orb => {
            orb.x += orb.dx;
            orb.y += orb.dy;

            if (orb.x < -orb.r) orb.x = canvas.width + orb.r;
            if (orb.x > canvas.width + orb.r) orb.x = -orb.r;
            if (orb.y < -orb.r) orb.y = canvas.height + orb.r;
            if (orb.y > canvas.height + orb.r) orb.y = -orb.r;

            const grad = ctx2.createRadialGradient(orb.x, orb.y, 0, orb.x, orb.y, orb.r);
            grad.addColorStop(0, `rgba(${orb.color}, ${orb.alpha})`);
            grad.addColorStop(1, `rgba(${orb.color}, 0)`);

            ctx2.beginPath();
            ctx2.arc(orb.x, orb.y, orb.r, 0, Math.PI * 2);
            ctx2.fillStyle = grad;
            ctx2.fill();
        });

        requestAnimationFrame(drawOrbs);
    }

    drawOrbs();

    window.addEventListener("mousemove", (e) => {
        orbs.forEach(orb => {
            const dx = e.clientX - orb.x;
            const dy = e.clientY - orb.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 300) {
                orb.dx += dx * 0.00008;
                orb.dy += dy * 0.00008;
                const speed = Math.sqrt(orb.dx * orb.dx + orb.dy * orb.dy);
                if (speed > 1.2) {
                    orb.dx = (orb.dx / speed) * 1.2;
                    orb.dy = (orb.dy / speed) * 1.2;
                }
            }
        });
    }, { passive: true });

})();