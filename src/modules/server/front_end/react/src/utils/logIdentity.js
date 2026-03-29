export function getLogIdentity(log, fallbackIndex = 0) {
  const id = String(log?.id ?? "").trim();
  if (id) {
    return `id:${id}`;
  }

  const time = String(log?.time ?? log?.occurrence_time ?? "").trim();
  const title = String(log?.title ?? "").trim();
  const description = String(log?.description ?? log?.system_label ?? "").trim();

  return `meta:${time}|${title}|${description}|${fallbackIndex}`;
}

export function findLogIndex(logs, targetLog) {
  if (!Array.isArray(logs) || logs.length === 0 || !targetLog) {
    return -1;
  }

  const targetId = String(targetLog?.id ?? "").trim();
  if (targetId) {
    const idIndex = logs.findIndex((item) => String(item?.id ?? "").trim() === targetId);
    if (idIndex >= 0) {
      return idIndex;
    }
  }

  const targetTime = String(targetLog?.time ?? targetLog?.occurrence_time ?? "").trim();
  const targetTitle = String(targetLog?.title ?? "").trim();

  if (!targetTime && !targetTitle) {
    return -1;
  }

  return logs.findIndex((item) => {
    const itemTime = String(item?.time ?? item?.occurrence_time ?? "").trim();
    const itemTitle = String(item?.title ?? "").trim();
    return itemTime === targetTime && itemTitle === targetTitle;
  });
}
