(function () {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    document.documentElement.classList.add("motion-ready");

    if (reducedMotion) {
        document.querySelectorAll("[data-count]").forEach((item) => {
            item.textContent = `${item.dataset.prefix || ""}${item.dataset.count || "0"}${item.dataset.suffix || ""}`;
        });
        return;
    }

    const revealItems = document.querySelectorAll(
        ".auth-hero, .auth-card, .dashboard-nav, .hero-panel, .assistant-panel, .details-panel, .metric-card, .form-panel, .chart-panel, .table-panel, .leaderboard-hero, .podium-card, .admin-hero-panel, .stat-card"
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
})();
