import { Card, CardBody, Heading, List, ListItem, Stack, Text } from '@chakra-ui/react'

export default function EmptyState() {
  return (
    <Card variant="outline" borderStyle="dashed">
      <CardBody py={16}>
        <Stack spacing={3} align="center" textAlign="center" maxW="md" mx="auto">
          <Heading size="md">No document selected</Heading>
          <Text color="gray.500">
            Upload a clinical PDF on the left. The text is extracted, sent to the model, validated against the
            clinical schema, and shown here as patient details, diagnoses, medications and labs.
          </Text>
          <List fontSize="sm" color="gray.500" spacing={1}>
            <ListItem>Try the synthetic files in the samples folder.</ListItem>
          </List>
        </Stack>
      </CardBody>
    </Card>
  )
}
