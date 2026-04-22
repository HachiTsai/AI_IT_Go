// 檔案: Scripts/device_list.js
// 參數: input 是一個物件，包含 tag (要搜尋的標籤)

const tag = input.tag || "#Manual"; // 預設值
const pages = dv.pages(tag); // 抓取貼有該標籤的頁面

if (pages.length === 0) {
    dv.paragraph("⚠️ 找不到貼有 " + tag + " 的設備。");
} else {
    dv.table(
        ["設備編號", "標籤", "別名", "客戶", "廠別"], // 表頭
        pages.map(p => [
            p.file.link, 
            p.tags,
            p.aliases,
            p.client,
            p.factory
        ])
    );
}