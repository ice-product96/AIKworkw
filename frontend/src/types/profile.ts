export interface ClientPublicInfo {
  id: string
  display_name: string
  avatar_url: string | null
  level: number
  projects_posted: number
  hire_rate_percent: number
  company: string | null
}

export interface UserProfile {
  id: string
  email: string
  role: string
  display_name: string | null
  bio: string | null
  company: string | null
  location: string | null
  website: string | null
  developer_title: string | null
  avatar_url: string | null
  level: number
  projects_posted: number
  hire_rate_percent: number
  agents_count: number
  completed_as_client: number
  completed_as_developer: number
  created_at: string
}
