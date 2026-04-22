// 檔案: 00_Inbox/00_Dataview/Script/smart_related_R301.js
// 用途: 智慧尋找與當前筆記高度相關的檔案 (同目錄或同標籤)
// 參數: input.source (可選) - 限制搜尋範圍，預設為 '#R301'

// 1. 設定: 要排除的通用標籤 (避免關聯性太弱)
// 注意：Dataview 的 tags 屬性通常包含 '#', 所以這裡也建議加上 '#' 以確保正確過濾
const ignoredTags = ["#R301", "#RCMT_Johor_MLC01", "#Gemini_DDC", "#Manual"];

// 1.1 設定: 要排除的資料夾 (例如: 模板區、歸檔區)
const ignoredFolders = ["90_Programming", "00_Inbox"];

// 1.2 設定: 白名單資料夾 (即使在排除資料夾下，這些子資料夾也不會被排除)
const whitelistFolders = ["02_Dashboard", "88_base"];

// 1.3 設定: 白名單標籤 (帶有這些標籤的筆記不會被排除)
const whitelistTags = ["#重要", "#保留"];

// 2. 獲取當前筆記的資訊
const currentFile = dv.current().file;
// 安全獲取標籤，若無標籤則為空陣列
const currentTags = currentFile.tags || [];

// 過濾標籤：確保只保留非通用的特定標籤
// 我們同時檢查有沒有 # 的情況，增加魯棒性
const specificTags = currentTags.filter(t => {
    const tagStr = t.toString(); // 確保是字串
    return !ignoredTags.some(ignored => tagStr === ignored || ignored === "#" + tagStr || tagStr === "#" + ignored);
});

// 3. 設定搜尋範圍 (預設搜尋 #R301)
const searchSource = input.source || '#R301';

// 4. 執行搜尋
const related = dv.pages(searchSource)
    .where(p => p.file.path != currentFile.path) // 排除自己
    .where(p => {
        const folderPath = p.file.folder;
        const pageTags = p.file.tags || [];

        // 優先檢查白名單（資料夾或標籤）
        const isWhitelistedFolder = whitelistFolders.some(f => folderPath.startsWith(f));
        const hasWhitelistTag = whitelistTags.some(tag => pageTags.includes(tag));

        if (isWhitelistedFolder || hasWhitelistTag) {
            return true; // 符合白名單條件，直接通過
        }

        // 排除特定資料夾
        const isIgnoredFolder = ignoredFolders.some(f => folderPath.startsWith(f));
        if (isIgnoredFolder) return false;

        // 邏輯 A: 標籤重疊 (至少有一個特定標籤相同)
        const hasCommonTag = pageTags.some(t => specificTags.includes(t));

        // 邏輯 B: 在同一個子目錄
        const isSameFolder = folderPath == currentFile.folder;

        return hasCommonTag || isSameFolder;
    });

// 5. 渲染結果
if (related.length === 0) {
    dv.paragraph(`⚠️ 無相關文件 (來源: ${searchSource})`);
    // Debug 訊息 (可選，幫助排查)
    // dv.paragraph(`Debug: Current Folder: ${currentFile.folder}, Specific Tags: ${specificTags.join(", ")}`);
} else {
    dv.table(
        ["Service Name", "Aliases", "Type", "Tags"],
        related
            .sort(p => p.file.mtime, "desc")
            .limit(10) // 限制顯示 10 筆
            .map(p => [
                p.file.link,
                p.aliases,
                p.type,
                // 在表格中顯示標籤時，也過濾掉通用標籤，讓版面更乾淨
                (p.file.tags || []).filter(t => !ignoredTags.includes(t) && !ignoredTags.includes("#" + t)).join(", ")
            ])
    );
}