import { notificationClient } from "./client"
import type { NotificationList, NotificationResponse } from "@/types/api"

export async function getNotifications(
  skip = 0,
  limit = 20,
  unread_only?: boolean
): Promise<NotificationList> {
  const res = await notificationClient.get<NotificationList>("/notifications", {
    params: { skip, limit, ...(unread_only !== undefined ? { unread_only } : {}) },
  })
  return res.data
}

export async function markRead(id: string): Promise<NotificationResponse> {
  const res = await notificationClient.put<NotificationResponse>(
    `/notifications/${id}/read`
  )
  return res.data
}

export async function createReminder(
  customer_id: string,
  message?: string
): Promise<NotificationResponse> {
  const res = await notificationClient.post<NotificationResponse>(
    "/notifications/reminder",
    { customer_id, ...(message ? { message } : {}) }
  )
  return res.data
}
