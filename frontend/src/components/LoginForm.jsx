import { useState } from 'react'
import {
  Alert, AlertIcon, Button, Card, CardBody, FormControl, FormLabel, Heading, Input, Stack, Text,
} from '@chakra-ui/react'
import { login } from '../api'

export default function LoginForm({ onLoggedIn }) {
  const [username, setUsername] = useState('demo')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await login(username, password)
      onLoggedIn()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card maxW="sm" mx="auto" mt={{ base: 4, md: 16 }}>
      <CardBody>
        <form onSubmit={submit}>
          <Stack spacing={4}>
            <Stack spacing={1}>
              <Heading size="md">Sign in</Heading>
              <Text fontSize="sm" color="gray.500">Use the demo credentials from your backend .env</Text>
            </Stack>
            {error && <Alert status="error" borderRadius="md"><AlertIcon />{error}</Alert>}
            <FormControl isRequired>
              <FormLabel>Username</FormLabel>
              <Input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>Password</FormLabel>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                     autoComplete="current-password" />
            </FormControl>
            <Button type="submit" isLoading={loading}>Sign in</Button>
          </Stack>
        </form>
      </CardBody>
    </Card>
  )
}
