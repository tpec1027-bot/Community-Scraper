// ==========================================
// i智慧 社區二維透視 - 全自動極速爬蟲腳本
// ==========================================
// 請在已經進入「二維透視」分頁的情況下，將以下所有程式碼貼入 F12 的 Console 中執行。

(async function fetchAllPdfs() {
    console.log("🚀 [光速爬蟲] 開始執行：全社區 PDF 網址極速擷取...");

    // 檢查是否在二維透視
    const activeTab = document.querySelector('.tab-pane.active');
    if (!activeTab || !activeTab.id.includes('CommunityCase')) {
        alert("⚠️ 錯誤：請先切換到『二維透視』分頁再執行！");
        return;
    }

    const results = [];

    // 取得下拉選單
    const addrSelect = document.querySelector('select[name="selectAddrid"]') || document.querySelector('select#selectAddrid');
    if (!addrSelect) {
        console.error("❌ 找不到地址下拉選單");
        return;
    }

    const options = Array.from(addrSelect.options).filter(o => o.value !== "0"); // 排除「未歸類」或空值
    console.log(`📍 發現 ${options.length} 個地址，開始遍歷...`);

    // Helper: 等待
    const sleep = ms => new Promise(r => setTimeout(r, ms));

    for (let i = 0; i < options.length; i++) {
        const opt = options[i];
        const addrText = opt.innerText.trim();
        console.log(`\n▶️ 正在處理第 ${i + 1}/${options.length} 個地址: ${addrText}`);

        // 切換地址
        if (addrSelect.value !== opt.value) {
            addrSelect.value = opt.value;
            try {
                addrSelect.dispatchEvent(new Event('change', { bubbles: true }));
            } catch (e) { }
            await sleep(3000); // 這裡故意等久一點，讓 i智慧 的 AJAX 表格生出來
        }

        // 找尋當前畫面所有的藍色小人
        const dropdowns = document.querySelectorAll('td .dropdown:has(.icon-user)');
        console.log(`   👥 找到 ${dropdowns.length} 戶有小人圖示...`);

        for (let j = 0; j < dropdowns.length; j++) {
            const dropdown = dropdowns[j];

            // 1. 點擊展開小人選單
            const toggleBtn = dropdown.querySelector('a[data-toggle="dropdown"]');
            if (toggleBtn) {
                toggleBtn.click();
                await sleep(300); // 等待選單動畫
            }

            // 2. 找到選單裡的第一個擁有者並點擊
            const firstOwnerLink = dropdown.querySelector('ul.dropdown-menu li:first-child a');
            let ownerName = "未知";
            if (firstOwnerLink) {
                ownerName = firstOwnerLink.innerText.trim();
                firstOwnerLink.click();
                await sleep(1500); // 等待彈出視窗加載

                // 3. 在彈出視窗中尋找 PDF 連結
                // i智慧有兩種：直接是 <a> 或被包在 layer 彈窗的 iframe 裡
                // 我們找整個 document 裡最近打開的 pdf link
                let pdfHref = null;
                const pdfBtns = document.querySelectorAll('a[href*=".pdf/"], a[href*="/pdf/"]');
                if (pdfBtns.length > 0) {
                    // 通常最後一個是最新的彈窗裡的
                    pdfHref = pdfBtns[pdfBtns.length - 1].href;
                }

                if (pdfHref) {
                    results.push({
                        address: addrText,
                        owner: ownerName,
                        url: pdfHref
                    });
                    console.log(`   ✅ 成功擷取: [${addrText}] ${ownerName}`);
                } else {
                    console.log(`   ⚠️ 找不到 PDF 按鈕: [${addrText}] ${ownerName}`);
                }

                // 4. 關閉彈出視窗 (找 layui 的關閉按鈕，或是彈出層的右上角X)
                const closeBtn = document.querySelector('a.layui-layer-iclose') || document.querySelector('.layui-layer-setwin a');
                if (closeBtn) closeBtn.click();
                await sleep(400);

            } else {
                console.log(`   ⚠️ 這戶沒有所有權人紀錄`);
            }
        }
    }

    console.log(`\n🎉 擷取完成！總共獲得 ${results.length} 筆資料。`);

    if (results.length > 0) {
        // 自動下載成 JSON 檔案
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(results, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", "首馥_data.json");
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
        console.log("💾 已自動觸發 首馥_data.json 下載，請將它放進 Community-Scraper 資料夾。");
    } else {
        alert("沒有抓到任何資料，請確認畫面是否正常。");
    }
})();
