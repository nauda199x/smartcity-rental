function doGet(e) {
  const folderUrl = e.parameter.folderUrl;
  
  if (!folderUrl) {
    return ContentService.createTextOutput(JSON.stringify({ error: "Missing 'folderUrl' parameter" }))
                         .setMimeType(ContentService.MimeType.JSON);
  }
  
  const cache = CacheService.getScriptCache();
  const cacheKey = MD5(folderUrl);
  const cachedData = cache.get(cacheKey);
  
  if (cachedData != null) {
    return ContentService.createTextOutput(cachedData)
                         .setMimeType(ContentService.MimeType.JSON);
  }
  
  try {
    const folderId = extractFolderId(folderUrl);
    const folder = DriveApp.getFolderById(folderId);
    const files = folder.getFiles();
    let images = [];
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    
    while (files.hasNext()) {
      let file = files.next();
      if (allowedTypes.indexOf(file.getMimeType()) !== -1) {
        images.push({
          name: file.getName(),
          url: "https://lh3.googleusercontent.com/d/" + file.getId(),
          thumbnail: "https://lh3.googleusercontent.com/d/" + file.getId() + "=w400-h300-g-c"
        });
      }
    }
    
    // Sắp xếp theo tên từ A-Z
    images.sort((a, b) => a.name.localeCompare(b.name, undefined, {numeric: true, sensitivity: 'base'}));
    
    // Tối ưu hóa dữ liệu trả về cho client
    const result = images.map(img => ({ url: img.url, thumbnail: img.thumbnail }));
    const jsonResponse = JSON.stringify(result);
    
    cache.put(cacheKey, jsonResponse, 1200); // Cache 20 phút
    
    return ContentService.createTextOutput(jsonResponse)
                         .setMimeType(ContentService.MimeType.JSON);
                         
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: err.message, fallback: true, data: [] }))
                         .setMimeType(ContentService.MimeType.JSON);
  }
}

function extractFolderId(url) {
  const match = url.match(/[-\w]{25,}/);
  if (match && match[0]) return match[0];
  throw new Error("Invalid Google Drive Folder URL");
}

function MD5(input) {
  const rawHash = Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, input, Utilities.Charset.UTF_8);
  let output = "";
  for (let i = 0; i < rawHash.length; i++) {
    let v = rawHash[i];
    if (v < 0) v += 256;
    if (v < 16) output += "0";
    output += v.toString(16);
  }
  return output;
}
