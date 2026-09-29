import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { profileService } from '@/services/profileService'
import { useAuthStore } from '@/store/authStore'
import type { ProfileUpdatePayload } from '@/types'

export function useProfile() {
  const user = useAuthStore((s) => s.user)
  return useQuery({
    queryKey: ['profile', user?.id],
    queryFn: profileService.getProfile,
    staleTime: 1000 * 60 * 5,
    enabled: !!user?.id,
  })
}

export function useUpdateProfile() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (data: ProfileUpdatePayload) => profileService.updateProfile(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['profile'] })
      toast.success('Profile updated!')
    },
    onError: () => {
      toast.error('Failed to update profile.')
    },
  })
}
