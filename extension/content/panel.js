// 列表页筛选面板，放在 Shadow DOM 里与豆瓣样式互不干扰
(() => {
  const DRH = globalThis.DRH;

  const STYLE = `
    :host { all: initial; display: block; margin: 0 0 14px; }
    .panel {
      --background: #F9F9F7; --card: #FFFFFF; --muted: #F0EEE6; --foreground: #181818;
      --muted-foreground: #737373; --primary: #CC785C; --primary-hover: #B8664B; --border: #E8E6DC;
      --danger: #B4483A;
      font: 13px/1.55 -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      color: var(--foreground); background: var(--background); border: 1px solid var(--border);
      border-radius: 12px; padding: 12px 14px;
    }
    .head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
    .head h2 { font: 600 15px Georgia, "Songti SC", serif; margin: 0; }
    .stats { color: var(--muted-foreground); flex: 1; min-width: 120px; }
    .switch { display: inline-flex; align-items: center; gap: 4px; cursor: pointer; color: var(--muted-foreground); }
    button {
      font: inherit; cursor: pointer; border-radius: 8px; padding: 3px 10px;
      border: 1px solid var(--border); background: var(--card); color: var(--foreground);
    }
    button:hover { border-color: var(--primary); color: var(--primary); }
    button.primary { background: var(--primary); border-color: var(--primary); color: #fff; }
    button.primary:hover { background: var(--primary-hover); color: #fff; }
    button:disabled { opacity: .6; cursor: progress; }
    button.link { border: 0; background: none; padding: 0; color: var(--primary); text-decoration: underline; }
    .body { margin-top: 10px; display: grid; gap: 8px; }
    .body[hidden] { display: none; }
    .row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 14px; }
    .field { display: inline-flex; align-items: center; gap: 6px; }
    .lbl { color: var(--muted-foreground); }
    input[type=text], input[type=number], select {
      font: inherit; color: var(--foreground); background: var(--card); border: 1px solid var(--border);
      border-radius: 8px; padding: 3px 8px; min-width: 0;
    }
    input[type=text] { width: 150px; }
    input[type=number] { width: 72px; }
    input:focus, select:focus { outline: 2px solid var(--primary); outline-offset: -1px; }
    input[type=checkbox] { accent-color: var(--primary); margin: 0; }
    .checks label { display: inline-flex; align-items: center; gap: 4px; cursor: pointer; }
    .msg { color: var(--muted-foreground); }
    .msg.error { color: var(--danger); }
    .divider { border-top: 1px dashed var(--border); margin: 2px 0; }
  `;

  const CHECKS = [
    ["hideSeeking", "排除求租"],
    ["personalOnly", "只看个人直租 / 转租"],
    ["hideGirlsOnly", "排除限女生"],
    ["hideBoysOnly", "排除限男生"],
    ["hideDuplicates", "隐藏重复帖"],
    ["hideUnknownPrice", "隐藏未标价"],
    ["hideRejected", "隐藏已排除"],
    ["hideSeen", "隐藏已读"],
    ["onlyMarked", "只看已标记"],
  ];

  const h = (tag, props = {}, children = []) => {
    const node = document.createElement(tag);
    Object.assign(node, props);
    node.append(...children);
    return node;
  };

  DRH.createPanel = ({ filters, onChange, onLoadMore, onOpenOptions }) => {
    const host = h("div", { className: "drh-panel-host" });
    const root = host.attachShadow({ mode: "open" });
    let current = { ...filters };

    const emit = () => onChange({ ...current });
    let timer;
    const emitSoon = () => {
      clearTimeout(timer);
      timer = setTimeout(emit, 250);
    };

    const numberOrNull = (v) => (v === "" ? null : Math.max(0, Number(v)));

    const textInput = (key, placeholder) => {
      const input = h("input", { type: "text", value: current[key], placeholder });
      input.addEventListener("input", () => {
        current[key] = input.value;
        emitSoon();
      });
      return input;
    };
    const numberInput = (key, placeholder) => {
      const input = h("input", { type: "number", min: 0, step: 100, value: current[key] ?? "", placeholder });
      input.addEventListener("input", () => {
        current[key] = numberOrNull(input.value);
        emitSoon();
      });
      return input;
    };
    const checkbox = (key, text) => {
      const input = h("input", { type: "checkbox", checked: !!current[key] });
      input.addEventListener("change", () => {
        current[key] = input.checked;
        emit();
      });
      return h("label", {}, [input, text]);
    };

    const stats = h("span", { className: "stats" });
    const enabled = h("input", { type: "checkbox", checked: current.enabled });
    enabled.addEventListener("change", () => {
      current.enabled = enabled.checked;
      emit();
    });
    const toggle = h("button", { type: "button" });
    const body = h("div", { className: "body" });
    const syncCollapsed = () => {
      body.hidden = current.collapsed;
      toggle.textContent = current.collapsed ? "展开" : "收起";
    };
    toggle.addEventListener("click", () => {
      current.collapsed = !current.collapsed;
      syncCollapsed();
      emit();
    });

    const commuteRow = h("div", { className: "row checks" });
    const msg = h("span", { className: "msg" });
    const loadOne = h("button", { type: "button", className: "primary", textContent: "加载下一页" });
    const loadThree = h("button", { type: "button", textContent: "再加载 3 页" });
    loadOne.addEventListener("click", () => onLoadMore(1));
    loadThree.addEventListener("click", () => onLoadMore(3));

    body.append(
      h("div", { className: "row" }, [
        h("span", { className: "field" }, [h("span", { className: "lbl", textContent: "包含" }), textInput("include", "任一关键词，空格分隔")]),
        h("span", { className: "field" }, [h("span", { className: "lbl", textContent: "排除" }), textInput("exclude", "如：隔断 地下室")]),
        h("span", { className: "field" }, [
          h("span", { className: "lbl", textContent: "月租" }),
          numberInput("minPrice", "不限"),
          "–",
          numberInput("maxPrice", "不限"),
        ]),
      ]),
      h("div", { className: "row checks" }, CHECKS.map(([key, text]) => checkbox(key, text))),
      commuteRow,
      h("div", { className: "divider" }),
      h("div", { className: "row" }, [loadOne, loadThree, msg]),
    );

    root.append(
      h("style", { textContent: STYLE }),
      h("div", { className: "panel" }, [
        h("div", { className: "head" }, [
          h("h2", { textContent: "租房筛选" }),
          stats,
          h("label", { className: "switch" }, [enabled, "启用筛选"]),
          toggle,
        ]),
        body,
      ]),
    );
    syncCollapsed();

    return {
      host,
      setStats(text) {
        stats.textContent = text;
      },
      setMessage(text, isError = false) {
        msg.textContent = text;
        msg.className = isError ? "msg error" : "msg";
      },
      setLoading(loading) {
        loadOne.disabled = loadThree.disabled = loading;
      },
      setHasMore(hasMore) {
        loadOne.hidden = loadThree.hidden = !hasMore;
      },
      // settings 变化时重画通勤一行
      setCommute(settings, error) {
        commuteRow.replaceChildren();
        if (!settings.gaodeKey || !settings.target) {
          const link = h("button", { type: "button", className: "link", textContent: "设置工作地点" });
          link.addEventListener("click", onOpenOptions);
          commuteRow.append(h("span", { className: "lbl" }, ["想按通勤时间筛选？先", link, "（需要你自己的高德 Key）"]));
          return;
        }
        const select = h("select", {}, [
          h("option", { value: "", textContent: "不限" }),
          ...[20, 30, 45, 60, 90].map((m) => h("option", { value: m, textContent: `${m} 分钟内` })),
        ]);
        select.value = current.maxCommute ?? "";
        select.addEventListener("change", () => {
          current.maxCommute = select.value === "" ? null : Number(select.value);
          emit();
        });
        commuteRow.append(
          h("span", { className: "field" }, [h("span", { className: "lbl", textContent: `到「${settings.target.name}」公交` }), select]),
          checkbox("hideUnknownCommute", "隐藏无法定位的"),
        );
        if (error) commuteRow.append(h("span", { className: "msg error", textContent: error }));
      },
    };
  };
})();
